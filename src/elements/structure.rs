use crate::core::context::ParseContext;
use crate::core::exceptions::ParseException;
use crate::core::parser::{ParseResult, ParserElement, ParserKind};
use crate::core::results::ParseResults;
use std::sync::Arc;

/// Empty - always matches at the current position, consuming nothing.
pub struct Empty;

impl ParserElement for Empty {
    fn parse_impl<'a>(&self, _ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        Ok((loc, ParseResults::new()))
    }

    #[inline(always)]
    fn try_match_at(&self, _input: &str, loc: usize) -> Option<usize> {
        Some(loc)
    }
}

/// NoMatch - never matches.
pub struct NoMatch;

impl ParserElement for NoMatch {
    fn parse_impl<'a>(&self, _ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        Err(ParseException::new(loc, "NoMatch will never match"))
    }

    #[inline(always)]
    fn try_match_at(&self, _input: &str, _loc: usize) -> Option<usize> {
        None
    }
}

/// SkipTo - matches everything up to (but not including) a specified expression.
pub struct SkipTo {
    target: Arc<dyn ParserElement>,
}

impl SkipTo {
    pub fn new(target: Arc<dyn ParserElement>) -> Self {
        Self { target }
    }
}

impl ParserElement for SkipTo {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        let input = ctx.input();
        let mut pos = loc;
        while pos <= input.len() {
            if self.target.try_match_at(input, pos).is_some() {
                return Ok((pos, ParseResults::from_single(&input[loc..pos])));
            }
            pos += 1;
        }
        Err(ParseException::new(loc, "SkipTo: target not found"))
    }

    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let mut pos = loc;
        while pos <= input.len() {
            if self.target.try_match_at(input, pos).is_some() {
                return Some(pos);
            }
            pos += 1;
        }
        None
    }
}

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
                // Wrap inner results in a Group item so nesting is preserved
                Ok((new_loc, ParseResults::from_group(res)))
            }
            Err(e) => Err(e),
        }
    }

    /// Zero-alloc match — delegates to inner element
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        self.element.try_match_at(input, loc)
    }

    fn parser_kind(&self) -> ParserKind {
        ParserKind::Group
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

    fn parser_kind(&self) -> ParserKind {
        ParserKind::Suppress
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
        // Combine disables whitespace skipping for its inner elements (like pyparsing's leave_whitespace)
        let old_skip = ctx.skip_whitespace;
        ctx.skip_whitespace = false;
        let result = self.element.parse_impl(ctx, loc);
        ctx.skip_whitespace = old_skip;
        let (new_loc, _res) = result?;
        // Instead of joining individual tokens, just slice the original input
        let combined = &ctx.input()[loc..new_loc];
        Ok((new_loc, ParseResults::from_single(combined)))
    }

    /// Combine must use parse_impl for matching to correctly disable whitespace skipping.
    /// Without this, try_match_at would delegate to And's try_match_at which skips whitespace
    /// between elements, causing false positive matches in search_string.
    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let mut ctx = ParseContext::new(input);
        self.parse_impl(&mut ctx, loc).ok().map(|(end, _)| end)
    }
}
