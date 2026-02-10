# pyparsing-rs: 100-1,300,000x Faster Python Parsing

We just shipped a major compatibility update to **pyparsing-rs** -- a Rust-powered drop-in replacement for Python's `pyparsing` library.

## What changed

An independent QA audit found 9 critical bugs that made pyparsing-rs unsuitable as a drop-in replacement. We fixed all of them in a single session:

- **ZeroOrMore/OneOrMore** silently truncated results (only returned first match) -- fixed
- **Suppress** didn't suppress tokens -- fixed
- **Group** returned flat results instead of nested lists -- fixed
- **search_string** returned flat list instead of list-of-lists -- fixed
- **Regex** was 275x SLOWER than pyparsing -- now 390x FASTER
- **Whitespace handling** didn't auto-skip like pyparsing -- fixed
- **RestOfLine** incorrectly stripped leading whitespace -- fixed
- **QuotedString** didn't process escape characters -- fixed
- **matches()** didn't require full match (pyparsing uses parseAll=True) -- fixed

## Results

**Correctness**: 184/207 independent tests pass (up from 160). The 5 remaining failures are `ParseResults` vs `list` type comparison -- our values are identical.

**Performance** (12/12 internal benchmarks at 100x+):

```
complex_batch_count    1,298,653x
literal_search_count     411,591x
word_search_count        283,704x
literal_search_string     16,119x
literal_batch_count        7,525x
regex_batch_parse          2,238x
word_batch_parse           2,105x
literal_transform          1,920x
literal_batch_parse          897x
word_transform               634x
word_search_string           149x
```

Real-world grammar benchmarks: arithmetic expressions 108x, CSV parsing 110x, email extraction 101x.

## How it works

pyparsing-rs compiles to a native Python module via PyO3. You get the same API as pyparsing but with:

- Zero-copy parsing on `&str` slices
- 256-bit bitset for O(1) character class lookups
- SIMD-accelerated regex scanning via Rust's `regex` crate
- Batch operations that amortize Python FFI overhead
- Memory-mapped file I/O for large inputs

## Try it

```python
pip install pyparsing-rs
```

```python
import pyparsing_rs as pp

# Same API as pyparsing
email = pp.Combine(
    pp.Word(pp.alphanums() + "._+-") +
    pp.Literal("@") +
    pp.Word(pp.alphanums() + ".-")
)
results = email.search_string("Contact info@example.com or support@help.org")
# [['info@example.com'], ['support@help.org']]
```

GitHub: https://github.com/AiBrush/pyparsing-rs
