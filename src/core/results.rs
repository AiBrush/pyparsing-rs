use smallvec::SmallVec;
use std::sync::Arc;

/// A single item in parse results — either a token string or a nested group
#[derive(Debug, Clone)]
pub enum ParseResultItem {
    Token(Arc<str>),
    /// Group wraps inner items in a nested structure (uses Box for indirection)
    Group(Box<[ParseResultItem]>),
}

/// Parse results that can contain tokens and nested groups
#[derive(Debug, Clone)]
pub struct ParseResults {
    items: SmallVec<[ParseResultItem; 2]>,
}

impl Default for ParseResults {
    fn default() -> Self {
        Self {
            items: SmallVec::new(),
        }
    }
}

impl ParseResults {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn from_single(s: &str) -> Self {
        let mut items = SmallVec::new();
        items.push(ParseResultItem::Token(Arc::from(s)));
        Self { items }
    }

    /// Create a ParseResults containing a single Group item wrapping the inner results
    pub fn from_group(inner: ParseResults) -> Self {
        let mut items = SmallVec::new();
        items.push(ParseResultItem::Group(
            inner.items.into_vec().into_boxed_slice(),
        ));
        Self { items }
    }

    pub fn extend(&mut self, other: ParseResults) {
        self.items.extend(other.items);
    }

    /// Access the structured items (tokens and groups)
    pub fn items(&self) -> &[ParseResultItem] {
        &self.items
    }
}
