use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

mod core;
mod elements;
mod helpers;

use elements::literals::{Literal as RustLiteral, Keyword as RustKeyword};
use elements::chars::{Word as RustWord, RegexMatch};
use core::parser::ParserElement;

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
        self.inner.parse_string(s)
            .map(|r| r.as_list())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
    
    fn search_string(&self, s: &str) -> PyResult<Vec<Vec<String>>> {
        let results = self.inner.search_string(s);
        Ok(results.into_iter().map(|r| r.as_list()).collect())
    }
}

/// Keyword match element
#[pyclass(name = "Keyword")]
struct PyKeyword {
    inner: RustKeyword,
}

#[pymethods]
impl PyKeyword {
    #[new]
    fn new(s: &str) -> Self {
        Self { inner: RustKeyword::new(s) }
    }
    
    fn parse_string(&self, s: &str) -> PyResult<Vec<String>> {
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

#[pyfunction]
fn printables() -> &'static str {
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
}

/// pyparsing_rs module
#[pymodule]
fn pyparsing_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLiteral>()?;
    m.add_class::<PyKeyword>()?;
    m.add_class::<PyWord>()?;
    m.add_class::<PyRegex>()?;
    
    m.add_function(wrap_pyfunction!(alphas, m)?)?;
    m.add_function(wrap_pyfunction!(alphanums, m)?)?;
    m.add_function(wrap_pyfunction!(nums, m)?)?;
    m.add_function(wrap_pyfunction!(printables, m)?)?;
    
    m.add("__version__", "0.1.0")?;
    Ok(())
}
