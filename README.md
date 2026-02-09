# pyparsing-rs

[![CI](https://github.com/AiBrush/pyparsing-rs/actions/workflows/test.yml/badge.svg)](https://github.com/AiBrush/pyparsing-rs/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/pyparsing-rs?color=blue)](https://pypi.org/project/pyparsing-rs/)
[![Python](https://img.shields.io/pypi/pyversions/pyparsing-rs)](https://pypi.org/project/pyparsing-rs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/AiBrush/pyparsing-rs)](https://github.com/AiBrush/pyparsing-rs/releases)

High-performance parser combinator library written in Rust with Python bindings. Drop-in replacement for Python's [pyparsing](https://github.com/pyparsing/pyparsing) with **20-40x faster** single parse calls and **500-16,000x faster** batch/search operations.

## Performance

All benchmarks compare against `pyparsing 3.3.2` on the same machine, same inputs, live baselines.

### Single `parse_string()` call

| Parser | pyparsing | pyparsing-rs | Speedup |
|--------|-----------|-------------|---------|
| Literal | 5.6 us | 0.3 us | **22x** |
| Keyword | 5.8 us | 0.3 us | **23x** |
| Word | 5.9 us | 0.3 us | **17x** |
| Regex | 7.3 us | 0.4 us | **19x** |
| Complex expr | 20.7 us | 0.5 us | **43x** |

### Batch `parse_batch()` (10K strings)

| Parser | pyparsing (loop) | pyparsing-rs | Speedup |
|--------|-----------------|-------------|---------|
| Literal | 41.0 ms | 0.05 ms | **849x** |
| Word | 46.9 ms | 0.03 ms | **1,772x** |
| Regex | 51.1 ms | 0.02 ms | **2,248x** |
| Complex expr | 91.8 ms | 0.04 ms | **2,219x** |

### `search_string()` (225KB text)

| Operation | pyparsing | pyparsing-rs | Speedup |
|-----------|-----------|-------------|---------|
| Literal search (5K matches) | 226.3 ms | 0.01 ms | **15,966x** |
| Word search (50K matches) | 253.8 ms | 0.13 ms | **1,930x** |
| Literal transform | 241.6 ms | 0.16 ms | **1,558x** |

## Installation

```bash
pip install pyparsing-rs
```

Pre-built wheels for Linux, macOS, and Windows across Python 3.9-3.13.

### From source

```bash
pip install maturin
git clone https://github.com/AiBrush/pyparsing-rs.git
cd pyparsing-rs
maturin develop --release
```

## Usage

```python
import pyparsing_rs as pp

# Basic elements
lit = pp.Literal("hello")
word = pp.Word(pp.alphas())
regex = pp.Regex(r"\d+")
kw = pp.Keyword("return")

# Combinators (via operators)
sequence = lit + word          # And
first_match = lit | word       # MatchFirst
longest_match = lit ^ word     # Or

# Repetition
zero_or_more = pp.ZeroOrMore(word)
one_or_more = pp.OneOrMore(word)
optional = pp.Opt(word)

# Result manipulation
grouped = pp.Group(word + word)
suppressed = pp.Suppress(lit)
combined = pp.Combine(word + word)

# Recursive grammars
expr = pp.Forward()
expr <<= word | pp.Literal("(") + expr + pp.Literal(")")

# Parse
result = lit.parse_string("hello world")
print(result.as_list())  # ['hello']

# Search
matches = word.search_string("hello world foo bar")

# Batch (process many strings at once)
results = word.parse_batch(["hello", "world", "foo"])
```

## Implemented Elements

| Category | Elements |
|----------|----------|
| **Literals** | `Literal`, `Keyword`, `CaselessLiteral`, `CaselessKeyword` |
| **Characters** | `Word`, `Char`, `Regex`, `QuotedString` |
| **Combinators** | `And` (+), `MatchFirst` (\|), `Or` (^) |
| **Repetition** | `ZeroOrMore`, `OneOrMore`, `Opt`/`Optional`, `Exactly` |
| **Structure** | `Group`, `Suppress`, `Combine`, `Forward` |
| **Positional** | `StringStart`, `StringEnd`, `LineStart`, `LineEnd` |
| **Special** | `Empty`, `NoMatch`, `SkipTo` |
| **Helpers** | `one_of()`, `alphas()`, `nums()`, `alphanums()`, `printables()` |

## Architecture

```
src/
  lib.rs              # PyO3 bindings
  core/
    parser.rs         # ParserElement trait
    context.rs        # Zero-copy parse context
    results.rs        # ParseResults (list + named captures)
    exceptions.rs     # ParseException
  elements/
    literals.rs       # Literal, Keyword, CaselessLiteral
    chars.rs          # Word, Char, Regex, QuotedString (256-bit CharSet)
    combinators.rs    # And, MatchFirst, Or
    repetition.rs     # ZeroOrMore, OneOrMore, Opt, Exactly
    structure.rs      # Group, Suppress, Combine
    forward.rs        # Forward (recursive grammars)
    positional.rs     # StringStart, StringEnd, LineStart, LineEnd
```

### Key optimizations

- **Zero-copy parsing**: `&str` slices over original input, no allocation
- **256-bit CharSet**: 4x64-bit bitset for O(1) ASCII character membership
- **First-byte fast path**: Literal matching checks first char before full comparison
- **SIMD search**: `memchr` crate for search_string and transform_string
- **Batch processing**: Amortize Python-Rust FFI overhead across thousands of inputs
- **Aggressive release profile**: LTO, single codegen unit, panic=abort, stripped symbols

## Development

```bash
# Build
maturin develop --release

# Test
pytest tests/ -v

# Benchmark
python tests/test_performance.py
```

## Links

- [PyPI](https://pypi.org/project/pyparsing-rs/) - Python package
- [GitHub](https://github.com/AiBrush/pyparsing-rs) - Source code and issues

## License

[MIT](LICENSE)
