use crate::core::parser::{ParserElement, ParseResult, next_parser_id};
use crate::core::context::ParseContext;
use crate::core::results::ParseResults;
use crate::core::exceptions::ParseException;
use memchr::memchr;

/// Match an exact literal string
pub struct Literal {
    id: usize,
    match_string: String,
    first_char: u8,
}

impl Literal {
    pub fn new(s: &str) -> Self {
        let first_char = s.bytes().next().unwrap_or(0);
        Self {
            id: next_parser_id(),
            match_string: s.to_string(),
            first_char,
        }
    }
}

impl ParserElement for Literal {
    #[inline(always)]
    fn parse_impl<'a>(
        &self,
        _ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = _ctx.input();
        let match_len = self.match_string.len();
        
        // Fast path: check length first
        if loc + match_len > input.len() {
            return Err(ParseException::new(
                loc,
                format!("Expected '{}'", self.match_string),
            ));
        }
        
        // Fast byte comparison
        let input_bytes = input.as_bytes();
        let match_bytes = self.match_string.as_bytes();
        
        // Check first byte quickly
        if input_bytes[loc] != self.first_char {
            return Err(ParseException::new(
                loc,
                format!("Expected '{}'", self.match_string),
            ));
        }
        
        // Check remaining bytes
        if match_len > 1 && input_bytes[loc + 1..loc + match_len] != match_bytes[1..] {
            return Err(ParseException::new(
                loc,
                format!("Expected '{}'", self.match_string),
            ));
        }
        
        let results = ParseResults::from_single(&self.match_string);
        Ok((loc + match_len, results))
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
    match_len: usize,
    first_char: u8,
    ident_chars: [bool; 256],
}

impl Keyword {
    pub fn new(s: &str) -> Self {
        let mut ident_chars = [false; 256];
        for c in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_" {
            ident_chars[*c as usize] = true;
        }
        
        let first_char = s.bytes().next().unwrap_or(0);
        
        Self {
            id: next_parser_id(),
            match_string: s.to_string(),
            match_len: s.len(),
            first_char,
            ident_chars,
        }
    }
}

impl ParserElement for Keyword {
    #[inline]
    fn parse_impl<'a>(
        &self,
        _ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = _ctx.input();
        let end_loc = loc + self.match_len;
        
        // Fast checks first
        if end_loc > input.len() {
            return Err(ParseException::new(
                loc,
                format!("Expected keyword '{}'", self.match_string),
            ));
        }
        
        let input_bytes = input.as_bytes();
        
        // Quick first char check
        if input_bytes[loc] != self.first_char {
            return Err(ParseException::new(
                loc,
                format!("Expected keyword '{}'", self.match_string),
            ));
        }
        
        // Check rest of string
        if self.match_len > 1 && &input[loc + 1..end_loc] != &self.match_string[1..] {
            return Err(ParseException::new(
                loc,
                format!("Expected keyword '{}'", self.match_string),
            ));
        }
        
        // Check word boundary after
        if end_loc < input.len() {
            let next_byte = input_bytes[end_loc];
            if self.ident_chars[next_byte as usize] {
                return Err(ParseException::new(
                    loc,
                    format!("Expected keyword '{}'", self.match_string),
                ));
            }
        }
        
        let results = ParseResults::from_single(&self.match_string);
        Ok((end_loc, results))
    }
    
    fn parser_id(&self) -> usize {
        self.id
    }
    
    fn name(&self) -> &str {
        &self.match_string
    }
}
