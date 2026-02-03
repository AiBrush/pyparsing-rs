

# pyparsing-rs

Rust rewrite of Python's `pyparsing` parser combinator library with pyo3 bindings. Target: **50-200x performance improvement** with 100% API compatibility.

## Mission

Work autonomously until 50x speedup is achieved on all benchmarks. Do not stop. Do not ask for permission. Iterate relentlessly.

## Environment

- **Rust**: stable toolchain
- **Project**: `/home/aibrush/pyparsing-rs`
- **Reference**: `/home/aibrush/pyparsing-original` (original pyparsing source + tests)

## Commands

```bash
# Build
maturin develop --release

# Test
python -m pytest tests/ -v

# Benchmark
python tests/test_performance.py

# Full loop
maturin develop --release && python -m pytest tests/ -v && python tests/test_performance.py

# Profile when stuck
cargo flamegraph --release

# Install Python packages
uv pip install <package>
```

## Architecture

```
src/
├── lib.rs              # pyo3 module entry point
├── core/               # Core infrastructure
│   ├── parser.rs       # ParserElement trait
│   ├── context.rs      # Parse context, position tracking
│   ├── results.rs      # ParseResults (list + dict)
│   ├── exceptions.rs   # ParseException
│   └── memoization.rs  # Packrat memoization
├── elements/           # Parser elements
│   ├── literals.rs     # Literal, Keyword, CaselessLiteral
│   ├── chars.rs        # Word, Char, CharsNotIn, Regex
│   ├── combinators.rs  # And, Or, MatchFirst
│   ├── repetition.rs   # ZeroOrMore, OneOrMore, Opt
│   ├── structure.rs    # Group, Suppress, Combine
│   └── forward.rs      # Forward (recursive grammars)
└── helpers/
    └── common.rs       # pyparsing_common equivalents
tests/
├── test_api_compat.py  # Must match original pyparsing behavior
└── test_performance.py # Benchmark comparisons (goal: 50x)
test_grammars/          # Sample grammars
```

## Implementation Priority

1. ParserElement trait → 2. Literal, Keyword → 3. Word, Regex → 
4. And, Or, MatchFirst → 5. ZeroOrMore, OneOrMore → 6. Group, Suppress → 7. Forward

## Code Rules

- **Zero-copy**: Use `&str` slices, return indices into original string
- **Inline hot paths**: `#[inline]` and `#[inline(always)]` on frequently called methods
- **Avoid dyn trait**: Use enum dispatch or generics for hot paths
- **Fast hashing**: Use FxHashMap from `rustc-hash` for memoization
- **API parity**: Same class names, methods, operators as original pyparsing
- **Cargo.toml**: Enable `lto = true`, `codegen-units = 1` in release profile

## Python API to Match

```python
import pyparsing_rs as pp

# Basic elements
lit = pp.Literal("hello")
word = pp.Word(pp.alphas(), pp.alphanums())
regex = pp.Regex(r"\d+")

# Combinators (via operators)
sequence = lit + word        # And
first_match = lit | word     # MatchFirst  
longest_match = lit ^ word   # Or

# Repetition
zero_or_more = pp.ZeroOrMore(word)
one_or_more = pp.OneOrMore(word)
optional = pp.Opt(word)

# Result manipulation
grouped = pp.Group(word + word)
suppressed = pp.Suppress(lit)
combined = pp.Combine(word + word)

# Recursive (Forward reference)
expr = pp.Forward()
expr <<= word | "(" + expr + ")"

# Parse
result = grammar.parse_string("input text")
result[0]          # List access
result["name"]     # Dict access (if named)
result.as_list()   # Convert to list
result.as_dict()   # Convert to dict
```

## Testing Strategy

1. Copy test files: `cp -r /home/aibrush/pyparsing-original/tests/* tests/`
2. Run baseline: `python baseline_benchmark.py` → saves `baseline_results.json`
3. Compare: Rust implementation must return identical data to original
4. Benchmark: Track speedup in `performance_results.json`

## Success Criteria

All must be true:
- [ ] All benchmarks show ≥50x speedup
- [ ] 100% of basic pyparsing tests pass
- [ ] Drop-in replacement API (same classes, methods, operators)
- [ ] Core elements: Literal, Word, Regex, And, Or, ZeroOrMore, Group, Forward

## Key Performance Optimizations

**Level 1** (do first):
- LTO + release builds
- `&str` instead of String
- Inline small functions

**Level 2** (when needed):
- Bitset for character class membership (O(1) lookup)
- Byte operations instead of char for ASCII
- SIMD scanning with `memchr` crate

**Level 3** (if still slow):
- Packrat memoization with FxHashMap
- Arena allocation for ParseResults
- Enum dispatch instead of dyn trait

## Important Notes

- Original pyparsing repo: `https://github.com/pyparsing/pyparsing`
- Test files are in `/home/aibrush/pyparsing-original/tests/`
- Original pyparsing is editable-installed; use `import pyparsing` for reference
- `import pyparsing_rs` for your Rust implementation
- Never sacrifice correctness for speed - tests must pass
- Profile before optimizing - don't guess bottlenecks

## pyparsing Key Concepts

### Operator Overloading
```python
a + b   # And (sequence)
a | b   # MatchFirst (first match wins)
a ^ b   # Or (longest match wins)
~a      # NotAny (negative lookahead)
a * 3   # Exactly 3 repetitions
```

### ParseResults
Dual list/dict access:
```python
result[0]        # First element
result["key"]    # Named element
result.key       # Attribute access
for item in result:  # Iteration
```

### Whitespace
pyparsing auto-skips whitespace by default. Respect this behavior.

### Parse Actions
User callbacks that transform results:
```python
integer = Word(nums).set_parse_action(lambda t: int(t[0]))
```


NOTE: our github repo is: https://github.com/aibrushcomputer/pyparsing-rs
