use crate::core::context::ParseContext;
use crate::core::exceptions::ParseException;
use crate::core::results::ParseResults;

/// Result of a parse attempt
pub type ParseResult<'a> = Result<(usize, ParseResults), ParseException>;

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

    /// Parse a string from the beginning
    fn parse_string(&self, input: &str) -> Result<ParseResults, ParseException> {
        let mut ctx = ParseContext::new(input);
        let (_, results) = self.parse_impl(&mut ctx, 0)?;
        Ok(results)
    }
}
