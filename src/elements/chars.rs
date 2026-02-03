use crate::core::parser::{ParserElement, ParseResult, next_parser_id};
use crate::core::context::ParseContext;
use crate::core::results::ParseResults;
use crate::core::exceptions::ParseException;

/// Match a word made up of characters from specified set
pub struct Word {
    id: usize,
    init_chars: Vec<char>,
    body_chars: Vec<char>,
    min_len: usize,
    max_len: usize,
    name: String,
}

impl Word {
    pub fn new(init_chars: &str) -> Self {
        let chars: Vec<char> = init_chars.chars().collect();
        let name = format!("W:({}...)", &init_chars[..init_chars.len().min(8)]);
        
        Self {
            id: next_parser_id(),
            init_chars: chars.clone(),
            body_chars: chars,
            min_len: 1,
            max_len: 0,  // 0 means unlimited
            name,
        }
    }
    
    pub fn with_body_chars(mut self, body: &str) -> Self {
        self.body_chars = body.chars().collect();
        self
    }
    
    #[inline(always)]
    fn is_init_char(&self, c: char) -> bool {
        self.init_chars.contains(&c)
    }
    
    #[inline(always)]
    fn is_body_char(&self, c: char) -> bool {
        self.body_chars.contains(&c)
    }
}

impl ParserElement for Word {
    #[inline]
    fn parse_impl<'a>(
        &self,
        _ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = _ctx.input();
        
        if loc >= input.len() {
            return Err(ParseException::new(loc, format!("Expected {}", self.name)));
        }
        
        let chars: Vec<char> = input[loc..].chars().collect();
        
        if chars.is_empty() {
            return Err(ParseException::new(loc, format!("Expected {}", self.name)));
        }
        
        // Check first character
        if !self.is_init_char(chars[0]) {
            return Err(ParseException::new(loc, format!("Expected {}", self.name)));
        }
        
        // Match body characters
        let mut match_len = chars[0].len_utf8();
        for (i, &c) in chars[1..].iter().enumerate() {
            if !self.is_body_char(c) {
                break;
            }
            if self.max_len > 0 && i + 2 > self.max_len {
                break;
            }
            match_len += c.len_utf8();
        }
        
        // Check minimum length
        if self.min_len > 0 {
            let char_count = input[loc..loc + match_len].chars().count();
            if char_count < self.min_len {
                return Err(ParseException::new(loc, format!("Expected {}", self.name)));
            }
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
            id: next_parser_id(),
            pattern: regex::Regex::new(&anchored)?,
            pattern_str: pattern.to_string(),
        })
    }
}

impl ParserElement for RegexMatch {
    #[inline]
    fn parse_impl<'a>(
        &self,
        _ctx: &mut ParseContext<'a>,
        loc: usize,
    ) -> ParseResult<'a> {
        let input = &_ctx.input()[loc..];
        
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
