use crate::core::context::{skip_ws, ParseContext};
use crate::core::exceptions::ParseException;
use crate::core::parser::{ParseResult, ParserElement, ParserKind};
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
        let input = ctx.input();

        for elem in self.elements.iter() {
            // Skip whitespace before each element (like pyparsing's preParse),
            // unless ctx.skip_whitespace is false (e.g., inside Combine)
            if ctx.skip_whitespace && elem.skip_whitespace_before() {
                loc = skip_ws(input, loc);
            }
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
        for elem in self.elements.iter() {
            // Skip whitespace before each element
            if elem.skip_whitespace_before() {
                pos = skip_ws(input, pos);
            }
            pos = elem.try_match_at(input, pos)?;
        }
        Some(pos)
    }

    fn parser_kind(&self) -> ParserKind {
        ParserKind::Complex
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

    fn parser_kind(&self) -> ParserKind {
        ParserKind::Complex
    }
}
