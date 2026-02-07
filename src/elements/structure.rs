use crate::core::context::ParseContext;
use crate::core::exceptions::ParseException;
use crate::core::parser::{ParseResult, ParserElement};
use crate::core::results::ParseResults;
use std::sync::Arc;

/// Group - wraps results in a nested structure
pub struct Group {
    element: Arc<dyn ParserElement>,
}

impl Group {
    pub fn new(element: Arc<dyn ParserElement>) -> Self {
        Self { element }
    }
}

impl ParserElement for Group {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        match self.element.parse_impl(ctx, loc) {
            Ok((new_loc, res)) => {
                // Group just passes through the tokens (grouping is semantic at the Python level)
                Ok((new_loc, res))
            }
            Err(e) => Err(e),
        }
    }

    /// Zero-alloc match — delegates to inner element
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        self.element.try_match_at(input, loc)
    }
}

/// Suppress - matches but doesn't add to results
pub struct Suppress {
    element: Arc<dyn ParserElement>,
}

impl Suppress {
    pub fn new(element: Arc<dyn ParserElement>) -> Self {
        Self { element }
    }
}

impl ParserElement for Suppress {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        // Use try_match_at to avoid creating ParseResults from inner element
        match self.element.try_match_at(ctx.input(), loc) {
            Some(new_loc) => Ok((new_loc, ParseResults::new())),
            None => Err(ParseException::new(loc, "Suppress: no match")),
        }
    }

    /// Zero-alloc match — delegates to inner element
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        self.element.try_match_at(input, loc)
    }
}

/// Combine - joins matched tokens into a single concatenated string.
/// Like pyparsing's Combine: `Combine(Word(alphas) + Literal("-") + Word(nums))`
/// would produce `["abc-123"]` instead of `["abc", "-", "123"]`.
pub struct Combine {
    element: Arc<dyn ParserElement>,
}

impl Combine {
    pub fn new(element: Arc<dyn ParserElement>) -> Self {
        Self { element }
    }
}

impl ParserElement for Combine {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        let (new_loc, _res) = self.element.parse_impl(ctx, loc)?;
        // Instead of joining individual tokens, just slice the original input
        let combined = &ctx.input()[loc..new_loc];
        Ok((new_loc, ParseResults::from_single(combined)))
    }

    /// Zero-alloc match — delegates to inner element
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        self.element.try_match_at(input, loc)
    }
}
