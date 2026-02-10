/// Context for parsing operations — holds a reference to the input string.
pub struct ParseContext<'a> {
    input: &'a str,
    /// Whether to auto-skip whitespace before element matches (pyparsing default: true).
    /// Set to false inside Combine to prevent whitespace skipping.
    pub skip_whitespace: bool,
}

impl<'a> ParseContext<'a> {
    pub fn new(input: &'a str) -> Self {
        Self {
            input,
            skip_whitespace: true,
        }
    }

    #[inline(always)]
    pub fn input(&self) -> &'a str {
        self.input
    }
}

/// Skip whitespace characters (space, tab, newline, carriage return) starting at `loc`.
/// Returns the position of the first non-whitespace character.
#[inline(always)]
pub fn skip_ws(input: &str, loc: usize) -> usize {
    let bytes = input.as_bytes();
    let mut pos = loc;
    while pos < bytes.len() && matches!(bytes[pos], b' ' | b'\t' | b'\n' | b'\r') {
        pos += 1;
    }
    pos
}
