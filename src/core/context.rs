/// Context for parsing operations — holds a reference to the input string.
pub struct ParseContext<'a> {
    input: &'a str,
}

impl<'a> ParseContext<'a> {
    pub fn new(input: &'a str) -> Self {
        Self { input }
    }

    #[inline(always)]
    pub fn input(&self) -> &'a str {
        self.input
    }
}
