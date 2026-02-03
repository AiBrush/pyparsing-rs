/// Context for parsing operations
pub struct ParseContext<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> ParseContext<'a> {
    pub fn new(input: &'a str) -> Self {
        Self { input, position: 0 }
    }

    #[inline(always)]
    pub fn input(&self) -> &'a str {
        self.input
    }

    #[inline(always)]
    pub fn position(&self) -> usize {
        self.position
    }

    #[inline(always)]
    pub fn set_position(&mut self, pos: usize) {
        self.position = pos;
    }

    #[inline(always)]
    pub fn remaining(&self) -> &'a str {
        &self.input[self.position..]
    }

    #[inline(always)]
    pub fn at_end(&self) -> bool {
        self.position >= self.input.len()
    }

    #[inline(always)]
    pub fn len(&self) -> usize {
        self.input.len()
    }
}
