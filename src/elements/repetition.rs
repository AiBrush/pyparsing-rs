use crate::core::context::ParseContext;
use crate::core::exceptions::ParseException;
use crate::core::parser::{ParseResult, ParserElement};
use crate::core::results::ParseResults;
use std::sync::Arc;

/// ZeroOrMore - matches 0 or more repetitions
pub struct ZeroOrMore {
    element: Arc<dyn ParserElement>,
}

impl ZeroOrMore {
    pub fn new(element: Arc<dyn ParserElement>) -> Self {
        Self { element }
    }
}

impl ParserElement for ZeroOrMore {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, mut loc: usize) -> ParseResult<'a> {
        let mut results = ParseResults::new();

        while let Ok((new_loc, res)) = self.element.parse_impl(ctx, loc) {
            if new_loc == loc {
                break;
            }
            results.extend(res);
            loc = new_loc;
        }

        Ok((loc, results))
    }

    /// Zero-alloc match — chains try_match_at through repetitions
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let mut pos = loc;
        while let Some(end) = self.element.try_match_at(input, pos) {
            if end == pos {
                break;
            }
            pos = end;
        }
        Some(pos)
    }
}

/// OneOrMore - matches 1 or more repetitions
pub struct OneOrMore {
    element: Arc<dyn ParserElement>,
}

impl OneOrMore {
    pub fn new(element: Arc<dyn ParserElement>) -> Self {
        Self { element }
    }
}

impl ParserElement for OneOrMore {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, mut loc: usize) -> ParseResult<'a> {
        let mut results = ParseResults::new();
        let mut count = 0;

        while let Ok((new_loc, res)) = self.element.parse_impl(ctx, loc) {
            if new_loc == loc {
                break;
            }
            results.extend(res);
            loc = new_loc;
            count += 1;
        }

        if count == 0 {
            Err(ParseException::new(loc, "Expected at least one match"))
        } else {
            Ok((loc, results))
        }
    }

    /// Zero-alloc match — requires at least one match, then repeats
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let mut pos = self.element.try_match_at(input, loc)?;
        while let Some(end) = self.element.try_match_at(input, pos) {
            if end == pos {
                break;
            }
            pos = end;
        }
        Some(pos)
    }
}

/// Optional - matches 0 or 1 times
pub struct Optional {
    element: Arc<dyn ParserElement>,
}

impl Optional {
    pub fn new(element: Arc<dyn ParserElement>) -> Self {
        Self { element }
    }
}

impl ParserElement for Optional {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        match self.element.parse_impl(ctx, loc) {
            Ok(result) => Ok(result),
            Err(_) => Ok((loc, ParseResults::new())),
        }
    }

    /// Zero-alloc match — returns inner match end or loc (always succeeds)
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        Some(self.element.try_match_at(input, loc).unwrap_or(loc))
    }
}

/// Exactly - matches exactly N repetitions of an element
pub struct Exactly {
    element: Arc<dyn ParserElement>,
    count: usize,
}

impl Exactly {
    pub fn new(element: Arc<dyn ParserElement>, count: usize) -> Self {
        Self { element, count }
    }
}

impl ParserElement for Exactly {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, mut loc: usize) -> ParseResult<'a> {
        let mut results = ParseResults::new();

        for _ in 0..self.count {
            let (new_loc, res) = self.element.parse_impl(ctx, loc)?;
            if new_loc == loc {
                return Err(ParseException::new(loc, "No progress in Exactly"));
            }
            results.extend(res);
            loc = new_loc;
        }

        Ok((loc, results))
    }

    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let mut pos = loc;
        for _ in 0..self.count {
            let end = self.element.try_match_at(input, pos)?;
            if end == pos {
                return None;
            }
            pos = end;
        }
        Some(pos)
    }
}
