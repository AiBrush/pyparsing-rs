# Project: pyparsing-rs - Rust Rewrite of Python pyparsing Library

## Mission

Rewrite the Python `pyparsing` parser combinator library in Rust with Python bindings (pyo3). Achieve **50-200x performance improvement** over the original while maintaining **100% API compatibility** for the core parsing operations.

Work autonomously and continuously until the goal is reached. Do not stop. Do not ask for permission. Iterate relentlessly.

---

## Why pyparsing-rs?

pyparsing is one of the most important parsing libraries in Python:
- **~270M monthly downloads** on PyPI
- Used to build parsers for configs, DSLs, data formats, protocols
- **Pure Python** - no C extensions, all CPU-bound parsing work
- **GitHub issue #490** explicitly requests Rust rewrite
- Users report 1.2s for 402 parse_string calls - unacceptably slow

The library's design (recursive descent parsing with backtracking) is computationally expensive in Python due to:
1. Heavy function call overhead (each parser element is a class with methods)
2. String slicing and copying on every match attempt
3. No native packrat memoization (optional, slow in Python)
4. ParseResults object construction on every match

All of these can be optimized to near-zero cost in Rust.

---

## Phase 0: Setup (Do This First)

### Python Environment

# Python build tools
uv pip install maturin pytest pytest-benchmark hypothesis

# Install original pyparsing for reference
uv pip install pyparsing

# Clone original pyparsing for source reference and tests
git clone https://github.com/pyparsing/pyparsing.git /home/aibrush/pyparsing-original
cd /home/aibrush/pyparsing-original
uv pip install -e .

# Create your project
mkdir -p /home/aibrush/pyparsing-rs
cd /home/aibrush/pyparsing-rs
maturin init --bindings pyo3
git init && git add -A && git commit -m "Initial setup"
```

### Project structure to create
```
/home/aibrush/pyparsing-rs/
├── Cargo.toml
├── pyproject.toml
├── src/
│   ├── lib.rs              # Main entry, Python module definition
│   ├── core/               # Core parsing infrastructure
│   │   ├── mod.rs
│   │   ├── parser.rs       # ParserElement base trait
│   │   ├── context.rs      # Parsing context, position tracking
│   │   ├── results.rs      # ParseResults equivalent
│   │   ├── exceptions.rs   # ParseException, ParseFatalException
│   │   └── memoization.rs  # Packrat memoization
│   ├── elements/           # Parser elements (the DSL)
│   │   ├── mod.rs
│   │   ├── literals.rs     # Literal, Keyword, CaselessLiteral, etc.
│   │   ├── chars.rs        # Word, Char, CharsNotIn, Regex
│   │   ├── combinators.rs  # And, Or, MatchFirst, Each
│   │   ├── repetition.rs   # ZeroOrMore, OneOrMore, Opt, Optional
│   │   ├── positional.rs   # LineStart, LineEnd, StringStart, StringEnd
│   │   ├── structure.rs    # Group, Suppress, Combine, Dict
│   │   ├── forward.rs      # Forward (recursive grammars)
│   │   ├── special.rs      # Empty, NoMatch, FollowedBy, NotAny
│   │   └── indented.rs     # IndentedBlock
│   ├── actions/            # Parse actions
│   │   ├── mod.rs
│   │   └── builtins.rs     # Common parse actions
│   ├── helpers/            # Helper functions
│   │   ├── mod.rs
│   │   ├── common.rs       # pyparsing_common equivalents
│   │   ├── unicode.rs      # pyparsing.unicode support
│   │   └── convenience.rs  # one_of, DelimitedList, etc.
│   └── python/             # Python bindings
│       ├── mod.rs
│       └── wrappers.rs     # PyO3 class wrappers
├── tests/
│   ├── test_api_compat.py  # Must pass all original pyparsing tests
│   ├── test_basic.py       # Basic functionality tests
│   └── test_performance.py # Benchmark comparisons
├── benches/
│   └── benchmarks.rs       # Rust-native benchmarks
└── test_grammars/          # Sample grammars for testing
    ├── arithmetic.py
    ├── json_grammar.py
    ├── sql_subset.py
    └── config_file.py
```

---

## Phase 1: Gather Test Assets and Baseline

### Step 1.1: Create test grammars
Create `/home/aibrush/pyparsing-rs/test_grammars/arithmetic.py`:
```python
#!/usr/bin/env python3
"""Simple arithmetic expression grammar for benchmarking."""
import pyparsing as pp

# Define grammar
integer = pp.Word(pp.nums)
real = pp.Combine(pp.Word(pp.nums) + "." + pp.Word(pp.nums))
number = real | integer
variable = pp.Word(pp.alphas, pp.alphanums + "_")

operand = number | variable
add_op = pp.one_of("+ -")
mul_op = pp.one_of("* /")

expr = pp.infix_notation(
    operand,
    [
        (mul_op, 2, pp.opAssoc.LEFT),
        (add_op, 2, pp.opAssoc.LEFT),
    ]
)

# Test data
TEST_EXPRESSIONS = [
    "1 + 2",
    "3 * 4 + 5",
    "x + y * z",
    "a * b + c * d",
    "(1 + 2) * 3",
    "10 / 2 - 3 + 4 * 5",
    "foo + bar * baz - qux / quux",
    "1.5 + 2.7 * 3.14159",
] * 50  # 400 expressions

def run_benchmark():
    """Parse all test expressions."""
    results = []
    for e in TEST_EXPRESSIONS:
        try:
            results.append(expr.parse_string(e))
        except pp.ParseException:
            pass
    return results

if __name__ == "__main__":
    import time
    start = time.perf_counter()
    run_benchmark()
    end = time.perf_counter()
    print(f"Parsed {len(TEST_EXPRESSIONS)} expressions in {end-start:.4f}s")
```

Create `/home/aibrush/pyparsing-rs/test_grammars/json_grammar.py`:
```python
#!/usr/bin/env python3
"""JSON-like grammar for benchmarking (without using built-in JSON)."""
import pyparsing as pp

# Define JSON grammar with pyparsing
LBRACE, RBRACE, LBRACK, RBRACK, COLON, COMMA = map(pp.Suppress, "{}[]:,")

json_string = pp.QuotedString('"', esc_char='\\')
json_number = pp.pyparsing_common.number
json_bool = pp.one_of("true false null").set_parse_action(
    lambda t: {"true": True, "false": False, "null": None}[t[0]]
)

json_value = pp.Forward()
json_array = pp.Group(LBRACK + pp.Optional(pp.DelimitedList(json_value)) + RBRACK)
json_object = pp.Dict(pp.Group(
    LBRACE + pp.Optional(pp.DelimitedList(
        pp.Group(json_string + COLON + json_value)
    )) + RBRACE
))

json_value <<= json_string | json_number | json_bool | json_array | json_object

# Test data
TEST_JSON = [
    '{"name": "John", "age": 30}',
    '{"list": [1, 2, 3, 4, 5]}',
    '{"nested": {"a": 1, "b": {"c": 2}}}',
    '{"mixed": [1, "two", true, null, {"key": "value"}]}',
    '{"empty_obj": {}, "empty_arr": []}',
] * 80  # 400 JSON objects

def run_benchmark():
    results = []
    for j in TEST_JSON:
        try:
            results.append(json_value.parse_string(j))
        except pp.ParseException:
            pass
    return results

if __name__ == "__main__":
    import time
    start = time.perf_counter()
    run_benchmark()
    end = time.perf_counter()
    print(f"Parsed {len(TEST_JSON)} JSON objects in {end-start:.4f}s")
```

Create `/home/aibrush/pyparsing-rs/test_grammars/config_file.py`:
```python
#!/usr/bin/env python3
"""INI-like config file grammar for benchmarking."""
import pyparsing as pp

# Config grammar
comment = pp.Regex(r"#.*").suppress()
key = pp.Word(pp.alphanums + "_")
value = pp.Regex(r"[^\n#]+").set_parse_action(lambda t: t[0].strip())
assignment = pp.Group(key + pp.Suppress("=") + value)
section_header = pp.Suppress("[") + pp.Word(pp.alphanums + "_") + pp.Suppress("]")
section = pp.Group(section_header + pp.Group(pp.ZeroOrMore(assignment | comment)))
config = pp.ZeroOrMore(section | comment)

# Test data
TEST_CONFIG = """
[database]
host = localhost
port = 5432
name = mydb
user = admin

[server]
host = 0.0.0.0
port = 8080
debug = true
workers = 4

[logging]
level = INFO
format = json
file = /var/log/app.log
""".strip()

# Repeat config for benchmarking
TEST_CONFIGS = [TEST_CONFIG] * 100

def run_benchmark():
    results = []
    for c in TEST_CONFIGS:
        try:
            results.append(config.parse_string(c))
        except pp.ParseException:
            pass
    return results

if __name__ == "__main__":
    import time
    start = time.perf_counter()
    run_benchmark()
    end = time.perf_counter()
    print(f"Parsed {len(TEST_CONFIGS)} configs in {end-start:.4f}s")
```

### Step 1.2: Create baseline benchmark script
Create `/home/aibrush/pyparsing-rs/baseline_benchmark.py`:
```python
#!/usr/bin/env python3
"""Baseline benchmarks for original pyparsing library."""
import time
import statistics
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "test_grammars"))

RESULTS_FILE = Path("/home/aibrush/pyparsing-rs/baseline_results.json")
ITERATIONS = 10

def benchmark(func, iterations=ITERATIONS):
    """Run function multiple times and return stats."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        func()
        end = time.perf_counter_ns()
        times.append(end - start)
    return {
        "mean_ns": statistics.mean(times),
        "median_ns": statistics.median(times),
        "min_ns": min(times),
        "max_ns": max(times),
        "stdev_ns": statistics.stdev(times) if len(times) > 1 else 0,
        "iterations": iterations
    }

def run_benchmarks():
    results = {}
    
    # Arithmetic expression benchmark
    print("Benchmarking arithmetic expressions...")
    from arithmetic import run_benchmark as arith_bench, TEST_EXPRESSIONS
    results["arithmetic"] = benchmark(arith_bench)
    results["arithmetic"]["num_parses"] = len(TEST_EXPRESSIONS)
    
    # JSON-like grammar benchmark
    print("Benchmarking JSON-like grammar...")
    from json_grammar import run_benchmark as json_bench, TEST_JSON
    results["json_grammar"] = benchmark(json_bench)
    results["json_grammar"]["num_parses"] = len(TEST_JSON)
    
    # Config file benchmark
    print("Benchmarking config file grammar...")
    from config_file import run_benchmark as config_bench, TEST_CONFIGS
    results["config_file"] = benchmark(config_bench)
    results["config_file"]["num_parses"] = len(TEST_CONFIGS)
    
    # Simple literal matching benchmark
    print("Benchmarking simple literals...")
    import pyparsing as pp
    literal = pp.Literal("hello")
    test_strings = ["hello world"] * 10000
    
    def literal_bench():
        for s in test_strings:
            try:
                literal.parse_string(s)
            except pp.ParseException:
                pass
    
    results["simple_literal"] = benchmark(literal_bench)
    results["simple_literal"]["num_parses"] = len(test_strings)
    
    # Word matching benchmark
    print("Benchmarking Word matching...")
    word = pp.Word(pp.alphas)
    test_words = ["helloworld", "foo", "bar", "testing", "pyparsing"] * 2000
    
    def word_bench():
        for w in test_words:
            try:
                word.parse_string(w)
            except pp.ParseException:
                pass
    
    results["word_match"] = benchmark(word_bench)
    results["word_match"]["num_parses"] = len(test_words)
    
    # Regex matching benchmark
    print("Benchmarking Regex matching...")
    regex = pp.Regex(r"\d{4}-\d{2}-\d{2}")
    test_dates = ["2024-01-15", "2023-12-31", "2025-06-30"] * 3000
    
    def regex_bench():
        for d in test_dates:
            try:
                regex.parse_string(d)
            except pp.ParseException:
                pass
    
    results["regex_match"] = benchmark(regex_bench)
    results["regex_match"]["num_parses"] = len(test_dates)
    
    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nBaseline results saved to {RESULTS_FILE}")
    print("\nSummary (mean times per batch):")
    for name, stats in results.items():
        per_parse = stats['mean_ns'] / stats['num_parses'] / 1000
        print(f"  {name}: {stats['mean_ns']/1e6:.2f} ms total, {per_parse:.2f} µs/parse")
    
    return results

if __name__ == "__main__":
    run_benchmarks()
```

### Step 1.3: Run baseline and record results
```bash
cd /home/aibrush/pyparsing-rs
python baseline_benchmark.py
cat baseline_results.json
```

**IMPORTANT**: Record these baseline numbers. Your goal is 50-200x improvement on each metric.

---

## Phase 2: Implement Core Rust Library

### Priority order (implement in this sequence):
1. **ParserElement trait** - Core parsing trait all elements implement
2. **Literal, Keyword** - Simple literal matching
3. **Word, Char, CharsNotIn** - Character class matching
4. **And (+), MatchFirst (|), Or (^)** - Combinators
5. **ZeroOrMore, OneOrMore, Opt/Optional** - Repetition
6. **Group, Suppress, Combine** - Result manipulation
7. **Forward** - Recursive grammar support
8. **ParseResults** - Result container with dict/list access
9. **Regex** - Regular expression matching
10. **ParseActions** - User-defined callbacks
11. **infix_notation** - Operator precedence parsing
12. **pyparsing_common** - Common expressions

### Implementation rules:

1. **Use zero-copy parsing wherever possible**
   - Use `&str` slices instead of copying strings
   - Return indices into original string
   - Only allocate for ParseResults

2. **Avoid function call overhead**
   - Use inline trait methods
   - Monomorphize hot paths
   - Consider enum dispatch instead of dyn trait

3. **Implement packrat memoization efficiently**
   - Use FxHashMap for fast hashing
   - Key by (position, parser_id)
   - Make memoization optional

4. **Match pyparsing's API exactly**
   - Same class names
   - Same method names  
   - Same operator overloads (+, |, ^, ~, *)
   - Same exceptions/errors

### Cargo.toml:
```toml
[package]
name = "pyparsing_rs"
version = "0.1.0"
edition = "2021"

[lib]
name = "pyparsing_rs"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
regex = "1.10"
once_cell = "1.19"
thiserror = "1.0"
rustc-hash = "2.0"  # Fast hashing
smallvec = "1.13"   # Stack-allocated small vectors
bstr = "1.9"        # Byte string utilities

[profile.release]
lto = true
codegen-units = 1
panic = "abort"
strip = true
opt-level = 3
```

### Example: Core parsing trait

Create `/home/aibrush/pyparsing-rs/src/core/parser.rs`:
```rust
use std::ops::{Add, BitOr, BitXor};
use crate::core::results::ParseResults;
use crate::core::exceptions::ParseException;
use crate::core::context::ParseContext;

/// Result of a parse attempt
pub type ParseResult<'a> = Result<(usize, ParseResults), ParseException>;

/// Core trait that all parser elements implement
pub trait ParserElement: Send + Sync {
    /// Attempt to parse at the given location
    fn parse_impl<'a>(
        &self,
        ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a>;
    
    /// Get a unique identifier for memoization
    fn parser_id(&self) -> usize;
    
    /// Human-readable name for error messages
    fn name(&self) -> &str;
    
    /// Parse a string from the beginning
    fn parse_string(&self, input: &str) -> Result<ParseResults, ParseException> {
        let mut ctx = ParseContext::new(input);
        let (_, results) = self.parse_impl(&mut ctx, 0)?;
        Ok(results)
    }
    
    /// Search for matches in a string
    fn search_string(&self, input: &str) -> Vec<ParseResults> {
        let mut ctx = ParseContext::new(input);
        let mut results = Vec::new();
        let mut loc = 0;
        
        while loc < input.len() {
            match self.parse_impl(&mut ctx, loc) {
                Ok((end_loc, res)) => {
                    results.push(res);
                    loc = end_loc;
                }
                Err(_) => {
                    loc += 1;
                }
            }
        }
        results
    }
    
    /// Transform results with a parse action
    fn set_parse_action<F>(&self, action: F) -> WithAction<Self, F>
    where
        Self: Sized,
        F: Fn(ParseResults) -> ParseResults,
    {
        WithAction { inner: self, action }
    }
    
    /// Set a name for the results
    fn set_results_name(&self, name: &str) -> Named<Self>
    where
        Self: Sized,
    {
        Named { inner: self, name: name.to_string() }
    }
}

/// Wrapper to add parse actions
pub struct WithAction<P, F> {
    inner: P,
    action: F,
}

/// Wrapper to name results
pub struct Named<P> {
    inner: P,
    name: String,
}
```

Create `/home/aibrush/pyparsing-rs/src/elements/literals.rs`:
```rust
use crate::core::parser::{ParserElement, ParseResult};
use crate::core::context::ParseContext;
use crate::core::results::ParseResults;
use crate::core::exceptions::ParseException;
use std::sync::atomic::{AtomicUsize, Ordering};

static PARSER_ID_COUNTER: AtomicUsize = AtomicUsize::new(0);

fn next_parser_id() -> usize {
    PARSER_ID_COUNTER.fetch_add(1, Ordering::Relaxed)
}

/// Match an exact literal string
pub struct Literal {
    id: usize,
    match_string: String,
}

impl Literal {
    pub fn new(s: &str) -> Self {
        Self {
            id: next_parser_id(),
            match_string: s.to_string(),
        }
    }
}

impl ParserElement for Literal {
    fn parse_impl<'a>(
        &self,
        ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = ctx.input();
        let match_len = self.match_string.len();
        
        if loc + match_len <= input.len() 
            && &input[loc..loc + match_len] == self.match_string 
        {
            let results = ParseResults::from_single(&self.match_string);
            Ok((loc + match_len, results))
        } else {
            Err(ParseException::new(
                loc,
                format!("Expected \"{}\"", self.match_string),
            ))
        }
    }
    
    fn parser_id(&self) -> usize {
        self.id
    }
    
    fn name(&self) -> &str {
        &self.match_string
    }
}

/// Match a keyword (literal with word boundary checking)
pub struct Keyword {
    id: usize,
    match_string: String,
    ident_chars: String,
}

impl Keyword {
    pub fn new(s: &str) -> Self {
        Self {
            id: next_parser_id(),
            match_string: s.to_string(),
            ident_chars: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_".to_string(),
        }
    }
}

impl ParserElement for Keyword {
    fn parse_impl<'a>(
        &self,
        ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = ctx.input();
        let match_len = self.match_string.len();
        let end_loc = loc + match_len;
        
        if end_loc <= input.len() 
            && &input[loc..end_loc] == self.match_string 
        {
            // Check word boundary after
            if end_loc < input.len() {
                let next_char = input[end_loc..].chars().next().unwrap();
                if self.ident_chars.contains(next_char) {
                    return Err(ParseException::new(
                        loc,
                        format!("Expected keyword \"{}\"", self.match_string),
                    ));
                }
            }
            
            let results = ParseResults::from_single(&self.match_string);
            Ok((end_loc, results))
        } else {
            Err(ParseException::new(
                loc,
                format!("Expected keyword \"{}\"", self.match_string),
            ))
        }
    }
    
    fn parser_id(&self) -> usize {
        self.id
    }
    
    fn name(&self) -> &str {
        &self.match_string
    }
}
```

Create `/home/aibrush/pyparsing-rs/src/elements/chars.rs`:
```rust
use crate::core::parser::{ParserElement, ParseResult};
use crate::core::context::ParseContext;
use crate::core::results::ParseResults;
use crate::core::exceptions::ParseException;

/// Match a word made up of characters from specified set
pub struct Word {
    id: usize,
    init_chars: String,
    body_chars: String,
    min_len: usize,
    max_len: usize,
    name: String,
}

impl Word {
    pub fn new(init_chars: &str) -> Self {
        Self {
            id: super::next_parser_id(),
            init_chars: init_chars.to_string(),
            body_chars: init_chars.to_string(),
            min_len: 1,
            max_len: 0,  // 0 means unlimited
            name: format!("W:({}...)", &init_chars[..init_chars.len().min(8)]),
        }
    }
    
    pub fn with_body_chars(mut self, body: &str) -> Self {
        self.body_chars = body.to_string();
        self
    }
}

impl ParserElement for Word {
    fn parse_impl<'a>(
        &self,
        ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = ctx.input();
        let chars: Vec<char> = input[loc..].chars().collect();
        
        if chars.is_empty() {
            return Err(ParseException::new(loc, format!("Expected {}", self.name)));
        }
        
        // Check first character
        if !self.init_chars.contains(chars[0]) {
            return Err(ParseException::new(loc, format!("Expected {}", self.name)));
        }
        
        // Match body characters
        let mut match_len = chars[0].len_utf8();
        for (i, &c) in chars[1..].iter().enumerate() {
            if !self.body_chars.contains(c) {
                break;
            }
            if self.max_len > 0 && i + 2 > self.max_len {
                break;
            }
            match_len += c.len_utf8();
        }
        
        let matched = &input[loc..loc + match_len];
        Ok((loc + match_len, ParseResults::from_single(matched)))
    }
    
    fn parser_id(&self) -> usize {
        self.id
    }
    
    fn name(&self) -> &str {
        &self.name
    }
}

/// Match using a regular expression
pub struct RegexMatch {
    id: usize,
    pattern: regex::Regex,
    pattern_str: String,
}

impl RegexMatch {
    pub fn new(pattern: &str) -> Result<Self, regex::Error> {
        let anchored = if pattern.starts_with('^') {
            pattern.to_string()
        } else {
            format!("^(?:{})", pattern)
        };
        
        Ok(Self {
            id: super::next_parser_id(),
            pattern: regex::Regex::new(&anchored)?,
            pattern_str: pattern.to_string(),
        })
    }
}

impl ParserElement for RegexMatch {
    fn parse_impl<'a>(
        &self,
        ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = &ctx.input()[loc..];
        
        if let Some(m) = self.pattern.find(input) {
            let matched = m.as_str();
            Ok((loc + matched.len(), ParseResults::from_single(matched)))
        } else {
            Err(ParseException::new(
                loc,
                format!("Expected match for /{}/", self.pattern_str),
            ))
        }
    }
    
    fn parser_id(&self) -> usize {
        self.id
    }
    
    fn name(&self) -> &str {
        &self.pattern_str
    }
}
```

Continue implementing the remaining elements...

---

## Phase 3: Python Bindings

`/home/aibrush/pyparsing-rs/src/lib.rs`:
```rust
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

mod core;
mod elements;
mod helpers;

use elements::literals::{Literal as RustLiteral, Keyword as RustKeyword};
use elements::chars::{Word as RustWord, RegexMatch};

/// Literal match element
#[pyclass(name = "Literal")]
struct PyLiteral {
    inner: RustLiteral,
}

#[pymethods]
impl PyLiteral {
    #[new]
    fn new(s: &str) -> Self {
        Self { inner: RustLiteral::new(s) }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        use core::parser::ParserElement;
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

/// Word match element
#[pyclass(name = "Word")]
struct PyWord {
    inner: RustWord,
}

#[pymethods]
impl PyWord {
    #[new]
    #[pyo3(signature = (init_chars, body_chars=None))]
    fn new(init_chars: &str, body_chars: Option<&str>) -> Self {
        let mut word = RustWord::new(init_chars);
        if let Some(body) = body_chars {
            word = word.with_body_chars(body);
        }
        Self { inner: word }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        use core::parser::ParserElement;
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

/// Regex match element
#[pyclass(name = "Regex")]
struct PyRegex {
    inner: RegexMatch,
}

#[pymethods]
impl PyRegex {
    #[new]
    fn new(pattern: &str) -> PyResult<Self> {
        RegexMatch::new(pattern)
            .map(|inner| Self { inner })
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        use core::parser::ParserElement;
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

// Character set constants
#[pyfunction]
fn alphas() -> &'static str {
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
}

#[pyfunction]
fn alphanums() -> &'static str {
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
}

#[pyfunction]
fn nums() -> &'static str {
    "0123456789"
}

/// pyparsing_rs module
#[pymodule]
fn pyparsing_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLiteral>()?;
    m.add_class::<PyWord>()?;
    m.add_class::<PyRegex>()?;
    
    m.add_function(wrap_pyfunction!(alphas, m)?)?;
    m.add_function(wrap_pyfunction!(alphanums, m)?)?;
    m.add_function(wrap_pyfunction!(nums, m)?)?;
    
    m.add("__version__", "0.1.0")?;
    Ok(())
}
```

---

## Phase 4: Testing

Create `/home/aibrush/pyparsing-rs/tests/test_performance.py`:
```python
#!/usr/bin/env python3
"""Performance benchmarks comparing pyparsing vs pyparsing_rs."""
import time
import json
import statistics
from pathlib import Path

BASELINE_FILE = Path("/home/aibrush/pyparsing-rs/baseline_results.json")
ITERATIONS = 10

def load_baseline():
    with open(BASELINE_FILE) as f:
        return json.load(f)

def benchmark(func, iterations=ITERATIONS):
    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        func()
        end = time.perf_counter_ns()
        times.append(end - start)
    return {"mean_ns": statistics.mean(times)}

def run_comparison():
    try:
        import pyparsing_rs as pp_rs
    except ImportError:
        print("ERROR: pyparsing_rs not built. Run: maturin develop --release")
        return
    
    baseline = load_baseline()
    results = {}
    
    # Simple literal benchmark
    print("\nBenchmarking Literal matching...")
    lit = pp_rs.Literal("hello")
    test_strings = ["hello world"] * 10000
    
    def literal_bench():
        for s in test_strings:
            try:
                lit.parse_string(s)
            except ValueError:
                pass
    
    rust_result = benchmark(literal_bench)
    orig = baseline.get("simple_literal", {})
    
    if orig:
        speedup = orig["mean_ns"] / rust_result["mean_ns"]
        results["simple_literal"] = {"speedup": speedup, "target_met": speedup >= 50}
        print(f"  Literal: {speedup:.1f}x speedup {'✓' if speedup >= 50 else '✗'}")
    
    # Word benchmark
    print("Benchmarking Word matching...")
    word = pp_rs.Word(pp_rs.alphas())
    test_words = ["helloworld", "foo", "bar", "testing", "pyparsing"] * 2000
    
    def word_bench():
        for w in test_words:
            try:
                word.parse_string(w)
            except ValueError:
                pass
    
    rust_result = benchmark(word_bench)
    orig = baseline.get("word_match", {})
    
    if orig:
        speedup = orig["mean_ns"] / rust_result["mean_ns"]
        results["word_match"] = {"speedup": speedup, "target_met": speedup >= 50}
        print(f"  Word: {speedup:.1f}x speedup {'✓' if speedup >= 50 else '✗'}")
    
    # Summary
    print("\n" + "="*50)
    all_met = all(r.get("target_met", False) for r in results.values())
    if all_met:
        print("🎉 ALL TARGETS MET! 50x+ improvement achieved!")
    else:
        not_met = [k for k, v in results.items() if not v.get("target_met")]
        print(f"Targets not yet met: {not_met}")
    
    with open("/home/aibrush/pyparsing-rs/performance_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_comparison()
```

---

## Success Criteria

You are DONE when ALL of these are true:

1. **Performance**: All benchmarks show ≥50x speedup over original pyparsing
2. **Compatibility**: Core pyparsing API is supported:
   - [ ] Literal, Keyword, CaselessLiteral
   - [ ] Word, Char, CharsNotIn, Regex
   - [ ] And (+), Or (^), MatchFirst (|)
   - [ ] ZeroOrMore, OneOrMore, Opt/Optional
   - [ ] Group, Suppress, Combine
   - [ ] Forward (recursive grammars)
   - [ ] ParseResults with dict/list access
3. **API Parity**: Same class names, methods, operators

---

## Key pyparsing Concepts

### Operator Overloading
- `+` = And (sequence)
- `|` = MatchFirst (first match wins)
- `^` = Or (longest match wins)
- `~` = NotAny (negative lookahead)

### ParseResults
Both a list and a dict:
```python
result[0]      # List-style access
result["key"]  # Dict-style access
result.as_list()
result.as_dict()
```

---

## IMPORTANT RULES

1. **Never stop** - If something fails, fix it and continue
2. **Never ask for permission** - You have full sudo access
3. **Commit often** - `git commit` after each milestone
4. **Benchmark constantly** - Run benchmarks after every change
5. **Tests must pass** - Never sacrifice correctness for speed

---

## Quick Start

```bash
mkdir pyparsing-rs && cd pyparsing-rs
maturin init --bindings pyo3

# Development loop
maturin develop --release && python -m pytest tests/ -v && python tests/test_performance.py
```

---

## BEGIN

Start now. Phase 0 first. Do not stop until 50x is achieved.

---

## Phase 5: CI/CD and PyPI Publishing

### Step 5.1: Create GitHub Actions CI workflow

Create `.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main, develop, 'feature/**', 'bugfix/**']
  pull_request:
    branches: [main, develop]

env:
  CACHE_TTL: 21600  # 6 hours in seconds

jobs:
  test-rust:
    name: Test Rust (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      
      - name: Cache cargo (6 hours)
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: "rust-cache"
          cache-directories: |
            ~/.cargo/registry
            ~/.cargo/git
            target
      
      - name: Check formatting
        run: cargo fmt --all -- --check
      
      - name: Run clippy
        run: cargo clippy --all -- -D warnings
      
      - name: Run tests
        run: cargo test --all

  test-python:
    name: Test Python (${{ matrix.os }}, ${{ matrix.python-version }})
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache pip dependencies (6 hours)
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-${{ matrix.python-version }}-
            ${{ runner.os }}-pip-
      
      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
      
      - name: Cache cargo (6 hours)
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: "rust-cache"
          cache-directories: |
            ~/.cargo/registry
            ~/.cargo/git
            target
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install maturin pytest
      
      - name: Build pyparsing_rs
        run: maturin build --release
      
      - name: Install pyparsing_rs
        run: pip install $(ls target/wheels/pyparsing_rs*.whl | head -1)
      
      - name: Run tests
        run: pytest tests/ -v
```

### Step 5.2: Create Release workflow

Create `.github/workflows/release.yml`:
```yaml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write

env:
  CACHE_TTL: 21600  # 6 hours in seconds

jobs:
  check-version:
    name: Check Version
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.get_version.outputs.version }}
      should_release: ${{ steps.check_tag.outputs.should_release }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Get version from Cargo.toml
        id: get_version
        run: |
          VERSION=$(grep '^version' Cargo.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Found version: $VERSION"
      
      - name: Check if tag exists
        id: check_tag
        run: |
          VERSION=${{ steps.get_version.outputs.version }}
          if git rev-parse "v$VERSION" >/dev/null 2>&1; then
            echo "Tag v$VERSION already exists"
            echo "should_release=false" >> $GITHUB_OUTPUT
          else
            echo "Tag v$VERSION does not exist - will release"
            echo "should_release=true" >> $GITHUB_OUTPUT
          fi

  test-before-release:
    name: Test Before Release
    needs: check-version
    if: needs.check-version.outputs.should_release == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      
      - name: Cache cargo (6 hours)
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: "rust-cache"
      
      - name: Check formatting
        run: cargo fmt --all -- --check
      
      - name: Run clippy
        run: cargo clippy --all -- -D warnings
      
      - name: Run Rust tests
        run: cargo test --all
      
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install maturin pytest
      
      - name: Build and test
        run: |
          maturin build --release
          pip install target/wheels/pyparsing_rs*.whl
          pytest tests/ -v

  build-wheels:
    name: Build Wheels (${{ matrix.os }}, py${{ matrix.python-version }})
    needs: [check-version, test-before-release]
    if: needs.check-version.outputs.should_release == 'true'
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
      
      - name: Cache cargo (6 hours)
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: "rust-cache"
      
      - name: Install maturin
        run: pip install maturin
      
      - name: Build wheel
        run: maturin build --release
      
      - name: Upload wheels
        uses: actions/upload-artifact@v4
        with:
          name: wheels-${{ matrix.os }}-py${{ matrix.python-version }}
          path: target/wheels/*.whl

  publish-pypi:
    name: Publish to PyPI
    needs: [check-version, test-before-release, build-wheels]
    if: needs.check-version.outputs.should_release == 'true'
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/pyparsing-rs
    permissions:
      id-token: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install maturin
        run: pip install maturin
      
      - name: Build source distribution
        run: maturin sdist
      
      - name: Publish to PyPI
        env:
          MATURIN_PYPI_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
        run: maturin publish --non-interactive

  create-release:
    name: Create GitHub Release
    needs: [check-version, publish-pypi]
    if: needs.check-version.outputs.should_release == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Download all wheels
        uses: actions/download-artifact@v4
        with:
          path: wheels
          pattern: wheels-*
      
      - name: Create and push tag
        run: |
          VERSION=${{ needs.check-version.outputs.version }}
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git tag "v$VERSION"
          git push origin "v$VERSION"
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ needs.check-version.outputs.version }}
          name: Release v${{ needs.check-version.outputs.version }}
          files: wheels/**/*.whl
          generate_release_notes: true
```

### Step 5.3: Configure PyPI token

Before first release:
1. Get PyPI API token from https://pypi.org/manage/account/token/
2. Add to GitHub repository secrets:
   - Go to repository Settings → Secrets and variables → Actions
   - Add secret: `PYPI_API_TOKEN`

### Step 5.4: Release workflow

1. Update version in `Cargo.toml` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Push to main
4. Release workflow automatically:
   - Runs all tests
   - Builds wheels for all platforms
   - Publishes to PyPI
   - Creates GitHub release with tag

---

## Success Checklist

- [ ] All benchmarks show ≥50x speedup
- [ ] 100% of basic pyparsing tests pass
- [ ] CI passes on all platforms
- [ ] Successfully published to PyPI
- [ ] GitHub release created with wheels
