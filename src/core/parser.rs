use crate::core::context::{skip_ws, ParseContext};
use crate::core::exceptions::ParseException;
use crate::core::results::ParseResults;

/// Result of a parse attempt
pub type ParseResult<'a> = Result<(usize, ParseResults), ParseException>;

/// Describes how a parser's results should be handled by parent combinators.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ParserKind {
    /// Normal parser — produces tokens from its match span (Literal, Word, Keyword, Regex, etc.)
    Normal,
    /// Suppress — matches but produces no tokens
    Suppress,
    /// Group — wraps its result tokens in a nested list
    Group,
    /// Complex — may produce multiple tokens (ZeroOrMore, OneOrMore, And, MatchFirst, Forward, etc.)
    /// Parent combinators must use parse_impl to get correct multi-token results.
    Complex,
}

/// Core trait that all parser elements implement
pub trait ParserElement: Send + Sync {
    /// Attempt to parse at the given location
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a>;

    /// Zero-alloc match check — returns end position without creating ParseResults.
    /// Override this for maximum performance on match-only operations.
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let mut ctx = ParseContext::new(input);
        self.parse_impl(&mut ctx, loc).map(|(end, _)| end).ok()
    }

    /// Parse a string from the beginning, skipping leading whitespace.
    fn parse_string(&self, input: &str) -> Result<ParseResults, ParseException> {
        let mut ctx = ParseContext::new(input);
        let loc = skip_ws(input, 0);
        let (_, results) = self.parse_impl(&mut ctx, loc)?;
        Ok(results)
    }

    /// How this parser's results should be handled by parent combinators.
    fn parser_kind(&self) -> ParserKind {
        ParserKind::Normal
    }

    /// Whether this parser should have whitespace skipped before it.
    /// Override to false for parsers like RestOfLine that capture whitespace.
    fn skip_whitespace_before(&self) -> bool {
        true
    }
}
