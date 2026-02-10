use crate::core::context::ParseContext;
use crate::core::exceptions::ParseException;
use crate::core::parser::{ParseResult, ParserElement, ParserKind};
use std::sync::{Arc, RwLock};

/// Forward - placeholder for recursive grammar definitions.
/// Allows defining a parser before its content is known.
pub struct Forward {
    inner: RwLock<Option<Arc<dyn ParserElement>>>,
}

impl Forward {
    pub fn new() -> Self {
        Self {
            inner: RwLock::new(None),
        }
    }

    pub fn set(&self, parser: Arc<dyn ParserElement>) {
        let mut guard = self.inner.write().unwrap();
        *guard = Some(parser);
    }
}

impl ParserElement for Forward {
    fn parse_impl<'a>(&self, ctx: &mut ParseContext<'a>, loc: usize) -> ParseResult<'a> {
        let guard = self.inner.read().unwrap();
        match guard.as_ref() {
            Some(parser) => parser.parse_impl(ctx, loc),
            None => Err(ParseException::new(loc, "Forward not initialized")),
        }
    }

    #[inline]
    fn try_match_at(&self, input: &str, loc: usize) -> Option<usize> {
        let guard = self.inner.read().unwrap();
        guard.as_ref()?.try_match_at(input, loc)
    }

    fn parser_kind(&self) -> ParserKind {
        ParserKind::Complex
    }
}
