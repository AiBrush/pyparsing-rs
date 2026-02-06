# Performance Baselines

## Latest Run: 2026-02-05 (Profiler Analysis Cycle)

| Benchmark | pyparsing (ms) | pyparsing_rs (ms) | Speedup |
|---|---|---|---|
| literal_batch_parse (10K) | 30.5 | 0.1 | 593.4x |
| word_batch_parse (10K) | 43.5 | 0.1 | 530.0x |
| regex_batch_parse (9K) | 43.1 | 0.1 | 735.0x |
| literal_search_string (225KB) | 224.7 | 0.1 | 2590.3x |
| word_search_string (250KB) | 231.2 | 1.1 | 207.4x |
| complex_batch_parse (5K) | 94.2 | 0.1 | 1011.5x |
| literal_search_count (225KB) | 225.0 | 0.1 | 3572.3x |
| word_search_count (250KB) | 228.3 | 0.2 | 987.1x |
| literal_batch_count (100K) | 313.9 | 0.1 | 2670.8x |
| complex_batch_count (50K) | 977.2 | 0.2 | 6266.8x |

**Summary: 10/10 benchmarks at 100x+, 10/10 at 50x+**

### Lowest speedup: word_search_string at 207.4x -- PRIMARY OPTIMIZATION TARGET

---

## Bottleneck Analysis

### Executive Summary

The `word_search_string` benchmark is the weakest at ~207x because it must
create **50,000 Python string objects** and a large PyList for each call.
By contrast, `word_search_count` (which returns a single integer) achieves
~987x. The ~4.8x gap between them is entirely Python object creation overhead.

### Micro-Benchmark Results: word_search_string Breakdown

#### 1. Scan vs Object Creation Cost (250KB text, 50K matches)

| Operation | Time | Notes |
|---|---|---|
| search_string_count (Rust scan only) | 241 us | Pure byte scanning, branchless state machine |
| search_string (scan + Python objects) | 1,200 us | Scan + build PyList of 50K PyStrings |
| Object creation overhead | 962 us | 5.0x the scan cost |
| Per-match object creation | 19 ns | Cost per PyString creation + PyList insert |

**Key insight**: At 250KB with 50K matches, 80% of the time in search_string
is spent creating Python objects, not scanning.

#### 2. Scaling: Object Creation Cost vs Text Size

| Text Size | Matches | Scan Time | Search Time | Overhead/match |
|---|---|---|---|---|
| 25KB | 5,000 | 25 us | 120 us | 19 ns |
| 250KB | 50,000 | 241 us | 1,200 us | 19 ns |
| 2.5MB | 500,000 | 2,430 us | 13,090 us | 21 ns |

The per-match overhead is stable at ~19-21 ns/match regardless of text size.
This is the cost of `PyString::new()` + hash table lookup + `PyList_SET_ITEM`.

#### 3. Cycle Detection Impact

| Text Type | Time | Notes |
|---|---|---|
| Cyclic (repeating period) | 1,170 us | Cycle detection + memcpy doubling |
| Non-cyclic (random seps) | 1,700 us | Full scan fallback |
| Cycle detection speedup | 1.46x | |

Cycle detection provides a meaningful 1.46x improvement. The benchmark text
("hello world foo bar baz " * 10000) is cyclic with a 24-byte period, which
helps. Non-cyclic text would show ~145x speedup instead of ~207x.

#### 4. Unique Word Count Impact

| Unique Words | Per-match Cost | Notes |
|---|---|---|
| 5 unique | 25 ns | Hash table fits easily (5-bit = 32 slots) |
| 100 unique | 29 ns | Overflows 5-bit hash table, more collisions |
| Cost increase | 1.19x | Modest -- hash table is not the bottleneck |

The 32-slot hash table for deduplication works well. Even with 100 unique
words (overflowing the 32 slots), per-match cost only increases 19%.

#### 5. Why Literal search_string is 12.5x Faster Than Word search_string

| Metric | Literal | Word |
|---|---|---|
| Speedup vs pyparsing | 2590x | 207x |
| Per-match cost | 19 ns | 22 ns |
| Matches in benchmark | 5,000 | 50,000 |
| Absolute rs time | 87 us | 1,100 us |

The apparent 12.5x speedup gap is misleading. The per-match costs are similar
(19 vs 22 ns). The real difference is:
- **Literal** uses `PySequence_Repeat` on a singleton list -- only creates
  1 unique Python string, then replicates it via C memcpy.
- **Word** creates unique PyStrings for each word found. Even with dedup
  (5 unique words), it still needs 50K PyList entries with INCREF + SET_ITEM.
- **10x more matches**: Word finds 50K matches vs Literal's 5K. More matches
  = more PyString operations.

### Single parse_string() Call Latency

| Parser | matches() | parse_string() | Overhead | vs pyparsing |
|---|---|---|---|---|
| Literal | 88 ns | 179 ns | 91 ns (2.0x) | 21.5x |
| Word | 85 ns | 212 ns | 127 ns (2.5x) | 22.8x |
| Regex | 147 ns | 339 ns | 192 ns (2.3x) | 19.8x |
| And (3 elements) | -- | 436 ns | -- | 51.6x |
| MatchFirst (1st) | -- | 325 ns | -- | 18.2x |

**Key insight**: The PyO3 call overhead (Python->Rust->Python) is ~88 ns.
parse_string adds ~90-190 ns for PyString + PyList creation. The parse
itself is essentially free -- it's all FFI and allocation overhead.

**Failure path is slow**: Exception creation costs 263-320 ns/call vs pyparsing's
2.5-3.5 us/call = only 7.8-13x speedup. Python exception objects are expensive.

### Reference: Python Object Creation Baseline

| Operation | Latency |
|---|---|
| Python noop() function call | 48 ns |
| Python `["hello"]` list creation | 149 ns |
| PyO3 matches() round-trip | 88 ns |
| PyString::new() + PyList (Literal parse_string) | 179 ns |

---

## Top 3 Optimization Opportunities

### Opportunity 1: Reduce word_search_string Per-Match Object Cost (HIGH IMPACT)

**Current state**: 19-21 ns/match for PyString creation + hash lookup + INCREF.

**Problem**: For the benchmark's 50K matches, this costs ~1ms of pure object
creation. The scan itself takes only ~0.24ms.

**Recommendations**:

A. **Return borrowed slices instead of PyString copies**: If we could return
   views into the original Python string object rather than creating new
   PyStrings, we'd eliminate most allocation. This requires PyO3's
   `PyString::new()` to be replaced with a mechanism to return substrings
   of the input. Unfortunately, CPython doesn't support string views/slices
   natively, so this isn't directly possible.

B. **Interning optimization**: Since the benchmark text has only 5 unique
   words, we already dedup via hash table. But we still call `Py_INCREF`
   once per match (50K INCREFs). Consider using a `PySequence_Repeat`-like
   approach: for each unique word, count its occurrences, then fill the
   output list in blocks using memcpy doubling (similar to Literal's approach).
   Current code already does this for cyclic text, but the fallback path
   (non-cyclic) still does per-item INCREF + SET_ITEM.

C. **Reduce PyList construction overhead**: Currently builds a `Vec<u8>` of
   indices, then iterates it to SET_ITEM. Consider building the list
   in-place during the scan to avoid the indices vector allocation.
   The indices vector for 50K matches = 50KB allocation that could be avoided.

**Estimated impact**: 20-40% improvement on word_search_string (from ~207x
to ~260-350x). The scan is already at ~1 GB/s throughput.

### Opportunity 2: Reduce parse_string Exception Path Cost (MEDIUM IMPACT)

**Current state**: Failed parse_string calls take 263-320 ns, with only
7.8-13x speedup over pyparsing (vs 20-30x for successful parses).

**Problem**: `PyValueError::new_err(...)` creates a Python exception object
with a formatted string. This is expensive because:
1. `format!("Expected '{}', ...")` allocates a Rust String
2. PyO3 converts it to a Python exception object
3. Python catches and discards it

**Recommendations**:

A. **Cache exception objects**: Pre-create the exception with a static message
   during parser construction (similar to how `error_msg: Arc<str>` is cached
   in Rust). Reuse the same Python exception object.

B. **Use a sentinel return instead of exceptions**: For internal use (like
   batch operations), return `None` or a specific sentinel instead of raising
   an exception. Only raise exceptions when the user calls parse_string directly.
   This is already done for `matches()` and `try_match_at()` but not parse_string.

**Estimated impact**: Could improve parse_string failure from 7.8x to ~15-20x.
Not a huge benchmark impact since the main benchmarks use batch operations,
but important for real-world single-string use cases.

### Opportunity 3: Optimize MatchFirst/And parse_string Return Values (MEDIUM IMPACT)

**Current state**: `MatchFirst.parse_string()` and several other combinators
use the old `self.inner.parse_string(s).map(|r| r.as_list())` path, which:
1. Creates Rust `ParseResults` with `SmallVec<[String; 2]>` (heap allocation for strings)
2. Converts to `Vec<String>` via `.as_list()` (another allocation)
3. PyO3 then converts `Vec<String>` to Python list of strings (third allocation)

Meanwhile, `PyLiteral.parse_string()` and `PyWord.parse_string()` use
direct PyList construction, skipping all intermediate allocations.

**Recommendations**:

A. **Rewrite MatchFirst.parse_string to use raw FFI**: Similar to how
   PyAnd.parse_string uses try_match_at + direct PyString::new, MatchFirst
   should do the same. Currently it goes through 3 allocation layers.

B. **Add `search_string` to MatchFirst and PyAnd**: These combinators don't
   have optimized search_string implementations. They fall back to the
   default trait implementation which creates ParseContext + ParseResults
   for every position.

**Estimated impact**: 1.5-2x improvement for MatchFirst.parse_string
single-call latency. Would bring it from 325 ns to ~200 ns.

---

## Micro-Benchmark Files

- `tests/bench_word_search.py` -- word_search_string bottleneck analysis
- `tests/bench_single_parse.py` -- single parse_string() call latency

## Previous Runs

### 2026-02-05 (Session Start - Before Profiling)

| Benchmark | Speedup |
|---|---|
| word_search_string | 176.1x |
| word_batch_parse | 405.9x |
| literal_batch_parse | 612.8x |
| regex_batch_parse | 791.8x |
| word_search_count | 952.6x |
| complex_batch_parse | 970.0x |
| literal_search_string | 2570.7x |
| literal_batch_count | 2882.2x |
| literal_search_count | 3653.7x |
| complex_batch_count | 6187.7x |
