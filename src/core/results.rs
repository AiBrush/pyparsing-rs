use std::collections::HashMap;

/// Parse results that can be accessed as both list and dict
#[derive(Debug, Clone, Default)]
pub struct ParseResults {
    tokens: Vec<String>,
    named: HashMap<String, usize>,
}

impl ParseResults {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn from_single(s: &str) -> Self {
        let mut r = Self::new();
        r.push(s);
        r
    }

    pub fn from_vec(tokens: Vec<String>) -> Self {
        Self {
            tokens,
            named: HashMap::new(),
        }
    }

    #[inline(always)]
    pub fn push(&mut self, token: &str) {
        self.tokens.push(token.to_string());
    }

    #[inline(always)]
    pub fn push_string(&mut self, token: String) {
        self.tokens.push(token);
    }

    pub fn set_name(&mut self, name: &str, index: usize) {
        self.named.insert(name.to_string(), index);
    }

    pub fn extend(&mut self, other: ParseResults) {
        let offset = self.tokens.len();
        self.tokens.extend(other.tokens);
        for (name, idx) in other.named {
            self.named.insert(name, idx + offset);
        }
    }

    pub fn as_list(&self) -> Vec<String> {
        self.tokens.clone()
    }

    pub fn as_vec(&self) -> &Vec<String> {
        &self.tokens
    }

    pub fn get(&self, index: usize) -> Option<&String> {
        self.tokens.get(index)
    }

    pub fn get_named(&self, name: &str) -> Option<&String> {
        self.named.get(name).and_then(|&idx| self.tokens.get(idx))
    }

    pub fn len(&self) -> usize {
        self.tokens.len()
    }

    pub fn is_empty(&self) -> bool {
        self.tokens.is_empty()
    }
}
