use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyList;
use std::sync::Arc;

mod core;
mod elements;
mod helpers;
mod compiler;
mod batch;
mod ultra_batch;
mod parallel_batch;
mod numpy_batch;
mod file_batch;
mod compiled_grammar;

use compiler::{CompiledGrammar, FastScanner};
use batch::{batch_parse_literals, batch_parse_words, batch_find_patterns, native_batch_parse};
use ultra_batch::{ultra_batch_literals, ultra_batch_words, ultra_batch_regex, massive_parse, benchmark_throughput, batch_scan_positions};
use parallel_batch::{parallel_match_literals, parallel_match_words, parallel_scan, max_throughput_benchmark, batch_transform_in_place, simd_batch_compare, batch_count_matches, unsafe_batch_match};
use numpy_batch::{aggregate_stats, match_to_bytes, match_indices, compact_results, length_histogram, streaming_batch_count};
use file_batch::{process_file_lines, process_files_parallel, file_grep, mmap_file_scan, process_csv_field, split_file_process};
use compiled_grammar::{FastParser, CharClassMatcher, ultra_fast_literal_match, swar_batch_match};

use elements::literals::{Literal as RustLiteral, Keyword as RustKeyword};
use elements::chars::{Word as RustWord, RegexMatch};
use elements::combinators::{And as RustAnd, MatchFirst as RustMatchFirst};
use elements::repetition::{ZeroOrMore as RustZeroOrMore, OneOrMore as RustOneOrMore, Optional as RustOptional};
use elements::structure::{Group as RustGroup, Suppress as RustSuppress};
use core::parser::ParserElement;

// ============================================================================
// Forward declarations of all pyclass structs
// ============================================================================

#[pyclass(name = "Literal")]
#[derive(Clone)]
struct PyLiteral {
    inner: Arc<RustLiteral>,
}

#[pyclass(name = "Word")]
#[derive(Clone)]
struct PyWord {
    inner: Arc<RustWord>,
}

#[pyclass(name = "Regex")]
#[derive(Clone)]
struct PyRegex {
    inner: Arc<RegexMatch>,
}

#[pyclass(name = "Keyword")]
#[derive(Clone)]
struct PyKeyword {
    inner: Arc<RustKeyword>,
}

#[pyclass(name = "And")]
#[derive(Clone)]
struct PyAnd {
    inner: Arc<RustAnd>,
}

#[pyclass(name = "MatchFirst")]
#[derive(Clone)]
struct PyMatchFirst {
    inner: Arc<RustMatchFirst>,
}

#[pyclass(name = "ZeroOrMore")]
#[derive(Clone)]
struct PyZeroOrMore {
    inner: Arc<RustZeroOrMore>,
}

#[pyclass(name = "OneOrMore")]
#[derive(Clone)]
struct PyOneOrMore {
    inner: Arc<RustOneOrMore>,
}

#[pyclass(name = "Optional")]
#[derive(Clone)]
struct PyOptional {
    inner: Arc<RustOptional>,
}

#[pyclass(name = "Group")]
#[derive(Clone)]
struct PyGroup {
    inner: Arc<RustGroup>,
}

#[pyclass(name = "Suppress")]
#[derive(Clone)]
struct PySuppress {
    inner: Arc<RustSuppress>,
}

// ============================================================================
// Implementations
// ============================================================================

#[pymethods]
impl PyLiteral {
    #[new]
    fn new(s: &str) -> Self {
        Self { inner: Arc::new(RustLiteral::new(s)) }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn parse_batch(&self, strings: Vec<String>) -> PyResult<Vec<Vec<String>>> {
        let results: Vec<Vec<String>> = strings.iter()
            .map(|s| {
                self.inner.parse_string(s.as_str())
                    .map(|r| r.as_list())
                    .unwrap_or_default()
            })
            .collect();
        Ok(results)
    }
    
    fn search_string(&self, s: &str) -> PyResult<Vec<Vec<String>>> {
        let results = self.inner.search_string(s);
        Ok(results.into_iter().map(|r| r.as_list()).collect())
    }
    
    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyAnd> {
        if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_and) = other.extract::<PyAnd>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_and.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for +"))
        }
    }
    
    fn __or__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyMatchFirst> {
        if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyMatchFirst { inner: Arc::new(RustMatchFirst::new(elements)) })
        } else if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyMatchFirst { inner: Arc::new(RustMatchFirst::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyMatchFirst { inner: Arc::new(RustMatchFirst::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for |"))
        }
    }
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
        Self { inner: Arc::new(word) }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn parse_batch(&self, strings: Vec<String>) -> PyResult<Vec<Vec<String>>> {
        let results: Vec<Vec<String>> = strings.iter()
            .map(|s| {
                self.inner.parse_string(s.as_str())
                    .map(|r| r.as_list())
                    .unwrap_or_default()
            })
            .collect();
        Ok(results)
    }
    
    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyAnd> {
        if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_and) = other.extract::<PyAnd>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_and.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for +"))
        }
    }
    
    fn __or__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyMatchFirst> {
        if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyMatchFirst { inner: Arc::new(RustMatchFirst::new(elements)) })
        } else if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyMatchFirst { inner: Arc::new(RustMatchFirst::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyMatchFirst { inner: Arc::new(RustMatchFirst::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for |"))
        }
    }
}

#[pymethods]
impl PyRegex {
    #[new]
    fn new(pattern: &str) -> PyResult<Self> {
        RegexMatch::new(pattern)
            .map(|inner| Self { inner: Arc::new(inner) })
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyAnd> {
        if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_and) = other.extract::<PyAnd>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_and.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_sup) = other.extract::<PySuppress>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_sup.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_regex) = other.extract::<PyRegex>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_regex.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for +"))
        }
    }
}

#[pymethods]
impl PyKeyword {
    #[new]
    fn new(s: &str) -> Self {
        Self { inner: Arc::new(RustKeyword::new(s)) }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

#[pymethods]
impl PyAnd {
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyAnd> {
        if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_and) = other.extract::<PyAnd>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_and.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for +"))
        }
    }
}

#[pymethods]
impl PyMatchFirst {
    #[new]
    fn new(exprs: &Bound<'_, PyList>) -> PyResult<Self> {
        let mut elements: Vec<Arc<dyn ParserElement>> = Vec::new();
        
        for i in 0..exprs.len() {
            let expr = exprs.get_item(i)?;
            
            if let Ok(lit) = expr.extract::<PyLiteral>() {
                elements.push(lit.inner);
            } else if let Ok(word) = expr.extract::<PyWord>() {
                elements.push(word.inner);
            } else if let Ok(mf) = expr.extract::<PyMatchFirst>() {
                elements.push(mf.inner);
            } else {
                return Err(PyValueError::new_err(format!("Unsupported expression type at index {}", i)));
            }
        }
        
        Ok(Self { inner: Arc::new(RustMatchFirst::new(elements)) })
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyAnd> {
        if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_and) = other.extract::<PyAnd>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_and.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for +"))
        }
    }
}

#[pymethods]
impl PyZeroOrMore {
    #[new]
    fn new(expr: &Bound<'_, PyAny>) -> PyResult<Self> {
        if let Ok(lit) = expr.extract::<PyLiteral>() {
            Ok(Self { inner: Arc::new(RustZeroOrMore::new(lit.inner)) })
        } else if let Ok(word) = expr.extract::<PyWord>() {
            Ok(Self { inner: Arc::new(RustZeroOrMore::new(word.inner)) })
        } else {
            Err(PyValueError::new_err("Unsupported expression type"))
        }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

#[pymethods]
impl PyOneOrMore {
    #[new]
    fn new(expr: &Bound<'_, PyAny>) -> PyResult<Self> {
        if let Ok(lit) = expr.extract::<PyLiteral>() {
            Ok(Self { inner: Arc::new(RustOneOrMore::new(lit.inner)) })
        } else if let Ok(word) = expr.extract::<PyWord>() {
            Ok(Self { inner: Arc::new(RustOneOrMore::new(word.inner)) })
        } else {
            Err(PyValueError::new_err("Unsupported expression type"))
        }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

#[pymethods]
impl PyOptional {
    #[new]
    fn new(expr: &Bound<'_, PyAny>) -> PyResult<Self> {
        if let Ok(lit) = expr.extract::<PyLiteral>() {
            Ok(Self { inner: Arc::new(RustOptional::new(lit.inner)) })
        } else if let Ok(word) = expr.extract::<PyWord>() {
            Ok(Self { inner: Arc::new(RustOptional::new(word.inner)) })
        } else {
            Err(PyValueError::new_err("Unsupported expression type"))
        }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

#[pymethods]
impl PyGroup {
    #[new]
    fn new(expr: &Bound<'_, PyAny>) -> PyResult<Self> {
        if let Ok(lit) = expr.extract::<PyLiteral>() {
            Ok(Self { inner: Arc::new(RustGroup::new(lit.inner)) })
        } else if let Ok(word) = expr.extract::<PyWord>() {
            Ok(Self { inner: Arc::new(RustGroup::new(word.inner)) })
        } else if let Ok(and) = expr.extract::<PyAnd>() {
            Ok(Self { inner: Arc::new(RustGroup::new(and.inner)) })
        } else {
            Err(PyValueError::new_err("Unsupported expression type"))
        }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyAnd> {
        if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_and) = other.extract::<PyAnd>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_and.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_sup) = other.extract::<PySuppress>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_sup.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_regex) = other.extract::<PyRegex>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_regex.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for +"))
        }
    }
}

#[pymethods]
impl PySuppress {
    #[new]
    fn new(expr: &Bound<'_, PyAny>) -> PyResult<Self> {
        if let Ok(lit) = expr.extract::<PyLiteral>() {
            Ok(Self { inner: Arc::new(RustSuppress::new(lit.inner)) })
        } else if let Ok(word) = expr.extract::<PyWord>() {
            Ok(Self { inner: Arc::new(RustSuppress::new(word.inner)) })
        } else {
            Err(PyValueError::new_err("Unsupported expression type"))
        }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn __add__(&self, other: &Bound<'_, PyAny>) -> PyResult<PyAnd> {
        if let Ok(other_word) = other.extract::<PyWord>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_word.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_lit) = other.extract::<PyLiteral>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_lit.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_and) = other.extract::<PyAnd>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_and.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_mf) = other.extract::<PyMatchFirst>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_mf.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_sup) = other.extract::<PySuppress>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_sup.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else if let Ok(other_regex) = other.extract::<PyRegex>() {
            let elements: Vec<Arc<dyn ParserElement>> = vec![self.inner.clone(), other_regex.inner.clone()];
            Ok(PyAnd { inner: Arc::new(RustAnd::new(elements)) })
        } else {
            Err(PyValueError::new_err("Unsupported operand type for +"))
        }
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

#[pyfunction]
fn printables() -> &'static str {
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
}

/// Batch parse multiple strings with a literal parser
#[pyfunction]
fn batch_parse_literal<'py>(
    py: Python<'py>,
    inputs: Bound<'py, PyAny>,
    literal: &str,
) -> PyResult<Bound<'py, PyList>> {
    let lit_bytes = literal.as_bytes();
    if lit_bytes.is_empty() {
        return Ok(PyList::empty(py));
    }
    let first_byte = lit_bytes[0];
    let lit_len = lit_bytes.len();
    
    let inputs_list: Vec<String> = inputs.extract()?;
    let results = PyList::new(py, inputs_list.iter().map(|input| {
        let input_bytes = input.as_bytes();
        let matched = input_bytes.len() >= lit_len 
            && input_bytes[0] == first_byte
            && &input_bytes[..lit_len] == lit_bytes;
        
        if matched {
            vec![literal.to_string()].to_object(py)
        } else {
            PyList::empty(py).to_object(py)
        }
    }))?;
    
    Ok(results)
}

/// High-performance compiled parser for batch operations
#[pyclass]
struct CompiledParser {
    grammar_type: String,
    pattern: String,
}

#[pymethods]
impl CompiledParser {
    #[new]
    fn new(grammar_type: &str, pattern: &str) -> Self {
        Self {
            grammar_type: grammar_type.to_string(),
            pattern: pattern.to_string(),
        }
    }
    
    fn parse_batch<'py>(&self, py: Python<'py>, inputs: Bound<'py, PyAny>) -> PyResult<Bound<'py, PyList>> {
        let inputs_list: Vec<String> = inputs.extract()?;
        
        let results = match self.grammar_type.as_str() {
            "literal" => {
                let lit_bytes = self.pattern.as_bytes();
                let first_byte = lit_bytes[0];
                let lit_len = lit_bytes.len();
                
                PyList::new(py, inputs_list.iter().map(|input| {
                    let input_bytes = input.as_bytes();
                    if input_bytes.len() >= lit_len 
                        && input_bytes[0] == first_byte
                        && &input_bytes[..lit_len] == lit_bytes {
                        vec![self.pattern.clone()].to_object(py)
                    } else {
                        PyList::empty(py).to_object(py)
                    }
                }))?
            }
            "word" => {
                let mut char_set = [false; 256];
                for c in self.pattern.chars() {
                    if (c as u32) < 256 {
                        char_set[c as usize] = true;
                    }
                }
                
                PyList::new(py, inputs_list.iter().map(|input| {
                    let bytes = input.as_bytes();
                    if bytes.is_empty() || !char_set[bytes[0] as usize] {
                        return PyList::empty(py).to_object(py);
                    }
                    
                    let mut i = 1;
                    while i < bytes.len() && char_set[bytes[i] as usize] {
                        i += 1;
                    }
                    
                    let matched = std::str::from_utf8(&bytes[..i]).unwrap_or("");
                    vec![matched.to_string()].to_object(py)
                }))?
            }
            _ => PyList::new(py, inputs_list.iter().map(|_| PyList::empty(py).to_object(py)))?,
        };
        
        Ok(results)
    }
}

/// pyparsing_rs module
#[pymodule]
fn pyparsing_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLiteral>()?;
    m.add_class::<PyKeyword>()?;
    m.add_class::<PyWord>()?;
    m.add_class::<PyRegex>()?;
    m.add_class::<PyAnd>()?;
    m.add_class::<PyMatchFirst>()?;
    m.add_class::<PyZeroOrMore>()?;
    m.add_class::<PyOneOrMore>()?;
    m.add_class::<PyOptional>()?;
    m.add_class::<PyGroup>()?;
    m.add_class::<PySuppress>()?;
    m.add_class::<CompiledParser>()?;
    
    m.add_function(wrap_pyfunction!(alphas, m)?)?;
    m.add_function(wrap_pyfunction!(alphanums, m)?)?;
    m.add_function(wrap_pyfunction!(nums, m)?)?;
    m.add_function(wrap_pyfunction!(printables, m)?)?;
    m.add_function(wrap_pyfunction!(batch_parse_literal, m)?)?;
    m.add_function(wrap_pyfunction!(batch_parse_literals, m)?)?;
    m.add_function(wrap_pyfunction!(batch_parse_words, m)?)?;
    m.add_function(wrap_pyfunction!(native_batch_parse, m)?)?;
    m.add_function(wrap_pyfunction!(ultra_batch_literals, m)?)?;
    m.add_function(wrap_pyfunction!(ultra_batch_words, m)?)?;
    m.add_function(wrap_pyfunction!(ultra_batch_regex, m)?)?;
    m.add_function(wrap_pyfunction!(massive_parse, m)?)?;
    m.add_function(wrap_pyfunction!(benchmark_throughput, m)?)?;
    m.add_function(wrap_pyfunction!(batch_scan_positions, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_match_literals, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_match_words, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_scan, m)?)?;
    m.add_function(wrap_pyfunction!(max_throughput_benchmark, m)?)?;
    m.add_function(wrap_pyfunction!(batch_count_matches, m)?)?;
    m.add_function(wrap_pyfunction!(aggregate_stats, m)?)?;
    m.add_function(wrap_pyfunction!(match_to_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(match_indices, m)?)?;
    m.add_function(wrap_pyfunction!(compact_results, m)?)?;
    m.add_function(wrap_pyfunction!(process_file_lines, m)?)?;
    m.add_function(wrap_pyfunction!(process_files_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(file_grep, m)?)?;
    m.add_function(wrap_pyfunction!(mmap_file_scan, m)?)?;
    m.add_class::<FastParser>()?;
    m.add_class::<CharClassMatcher>()?;
    m.add_function(wrap_pyfunction!(ultra_fast_literal_match, m)?)?;
    m.add_function(wrap_pyfunction!(swar_batch_match, m)?)?;
    
    m.add("__version__", "0.1.0")?;
    Ok(())
}
