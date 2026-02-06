use crate::core::context::ParseContext;
use crate::core::exceptions::ParseException;
use crate::core::parser::{ParseResult, ParserElement};
use crate::core::results::ParseResults;
use std::sync::Arc;

/// Sequence combinator - all must match in order (And)
pub struct And {
    elements: Vec<Arc<dyn ParserElement>>,
}

impl And {
    pub fn new(elements: Vec<Arc<dyn ParserElement>>) -> Self {
        Self { elements }
    }

    pub fn elements(&self) -> &[Arc<dyn ParserElement>] {
        &self.elements
    }
}

impl ParserElement for And {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, mut loc: usize) -> ParseResult<'a> {
        let mut results = ParseResults::new();

        for elem in &self.elements {
            match elem.parse_impl(ctx, loc) {
                Ok((new_loc, res)) => {
                    results.extend(res);
                    loc = new_loc;
                }
                Err(e) => return Err(e),
            }
        }

        Ok((loc, results))
    }

    /// Zero-alloc match — chains try_match_at through all elements
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let mut pos = loc;
        for elem in &self.elements {
            pos = elem.try_match_at(input, pos)?;
        }
        Some(pos)
    }

    /// Optimized search: use try_match_at pre-filter, then parse_impl for results
    fn search_string(&self, input: &str) -> Vec<ParseResults> {
        let mut ctx = ParseContext::new(input);
        let mut results = Vec::new();
        let mut loc = 0;

        while loc < input.len() {
            if self.try_match_at(input, loc).is_some() {
                if let Ok((end_loc, res)) = self.parse_impl(&mut ctx, loc) {
                    results.push(res);
                    loc = end_loc;
                    continue;
                }
            }
            loc += 1;
        }
        results
    }
}

/// MatchFirst combinator - first match wins (| operator)
pub struct MatchFirst {
    elements: Vec<Arc<dyn ParserElement>>,
}

impl MatchFirst {
    pub fn new(elements: Vec<Arc<dyn ParserElement>>) -> Self {
        Self { elements }
    }

    pub fn elements(&self) -> &[Arc<dyn ParserElement>] {
        &self.elements
    }
}

impl ParserElement for MatchFirst {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        let mut last_error = None;

        for elem in &self.elements {
            match elem.parse_impl(ctx, loc) {
                Ok(result) => return Ok(result),
                Err(e) => last_error = Some(e),
            }
        }

        Err(last_error.unwrap_or_else(|| ParseException::new(loc, "No match found")))
    }

    /// Zero-alloc match — tries each element in order, returns first match
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        for elem in &self.elements {
            if let Some(end) = elem.try_match_at(input, loc) {
                return Some(end);
            }
        }
        None
    }

    /// Optimized search: use try_match_at pre-filter, then parse_impl for results
    fn search_string(&self, input: &str) -> Vec<ParseResults> {
        let mut ctx = ParseContext::new(input);
        let mut results = Vec::new();
        let mut loc = 0;

        while loc < input.len() {
            if self.try_match_at(input, loc).is_some() {
                if let Ok((end_loc, res)) = self.parse_impl(&mut ctx, loc) {
                    results.push(res);
                    loc = end_loc;
                    continue;
                }
            }
            loc += 1;
        }
        results
    }
}
