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

class TestTransformString:
    def test_literal_transform(self):
        lit = pp.Literal("fox")
        result = lit.transform_string("The fox and the fox", "cat")
        assert result == "The cat and the cat"

    def test_literal_transform_no_match(self):
        lit = pp.Literal("fox")
        result = lit.transform_string("no matches here", "cat")
        assert result == "no matches here"

    def test_literal_transform_empty(self):
        lit = pp.Literal("fox")
        result = lit.transform_string("", "cat")
        assert result == ""

    def test_word_transform(self):
        word = pp.Word(pp.alphas())
        result = word.transform_string("hello world", "X")
        assert result == "X X"

    def test_regex_transform(self):
        regex = pp.Regex(r"\d+")
        result = regex.transform_string("foo 123 bar 456", "NUM")
        assert result == "foo NUM bar NUM"

class TestOneOf:
    def test_one_of_basic(self):
        expr = pp.one_of("+ - * /")
        assert expr.parse_string("+") == ["+"]
        assert expr.parse_string("-") == ["-"]
        assert expr.parse_string("*") == ["*"]
        assert expr.parse_string("/") == ["/"]

    def test_one_of_no_match(self):
        expr = pp.one_of("+ - * /")
        with pytest.raises(ValueError):
            expr.parse_string("x")

    def test_one_of_in_expr(self):
        num = pp.Word(pp.nums())
        op = pp.one_of("+ -")
        expr = num + op + num
        result = expr.parse_string("3+5")
        assert result == ["3", "+", "5"]

    def test_one_of_search(self):
        expr = pp.one_of("+ - * /")
        assert expr.search_string_count("1+2-3*4/5") == 4

    def test_one_of_empty_raises(self):
        with pytest.raises(ValueError):
            pp.one_of("")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
