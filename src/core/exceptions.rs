use std::fmt;

#[derive(Debug, Clone)]
pub struct ParseException {
    pub loc: usize,
    pub msg: String,
}

impl ParseException {
    pub fn new(loc: usize, msg: impl Into<String>) -> Self {
        Self {
            loc,
            msg: msg.into(),
        }
    }
}

impl fmt::Display for ParseException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "ParseException at position {}: {}", self.loc, self.msg)
    }
}

impl std::error::Error for ParseException {}

#[derive(Debug, Clone)]
pub struct ParseFatalException {
    pub loc: usize,
    pub msg: String,
}

impl ParseFatalException {
    pub fn new(loc: usize, msg: impl Into<String>) -> Self {
        Self {
            loc,
            msg: msg.into(),
        }
    }
}

impl fmt::Display for ParseFatalException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "ParseFatalException at position {}: {}", self.loc, self.msg)
    }
}

impl std::error::Error for ParseFatalException {}
