#!/usr/bin/env python3
"""Basic tests for pyparsing_rs."""
import pytest
import pyparsing_rs as pp

class TestLiteral:
    def test_literal_match(self):
        lit = pp.Literal("hello")
        result = lit.parse_string("hello world")
        assert result == ["hello"]
    
    def test_literal_no_match(self):
        lit = pp.Literal("hello")
        with pytest.raises(ValueError):
            lit.parse_string("goodbye world")
    
    def test_literal_at_start(self):
        lit = pp.Literal("hello")
        result = lit.parse_string("hello")
        assert result == ["hello"]

class TestWord:
    def test_word_alpha(self):
        word = pp.Word(pp.alphas())
        result = word.parse_string("hello")
        assert result == ["hello"]
    
    def test_word_alphanum(self):
        word = pp.Word(pp.alphanums())
        result = word.parse_string("hello123")
        assert result == ["hello123"]
    
    def test_word_with_body(self):
        word = pp.Word("abc", "xyz")
        result = word.parse_string("axxx")
        assert result == ["axxx"]

class TestRegex:
    def test_regex_digits(self):
        regex = pp.Regex(r"\d+")
        result = regex.parse_string("12345")
        assert result == ["12345"]
    
    def test_regex_date(self):
        regex = pp.Regex(r"\d{4}-\d{2}-\d{2}")
        result = regex.parse_string("2024-01-15")
        assert result == ["2024-01-15"]

class TestKeyword:
    def test_keyword_match(self):
        kw = pp.Keyword("if")
        result = kw.parse_string("if")
        assert result == ["if"]
    
    def test_keyword_no_partial(self):
        kw = pp.Keyword("if")
        with pytest.raises(ValueError):
            kw.parse_string("ifx")  # Should fail - "ifx" is not "if"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
