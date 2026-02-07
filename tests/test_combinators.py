#!/usr/bin/env python3
"""Test combinators for pyparsing_rs."""
import pytest
import pyparsing_rs as pp

class TestAnd:
    def test_and_sequence(self):
        lit1 = pp.Literal("hello")
        lit2 = pp.Literal(" world")
        combined = lit1 + lit2
        result = combined.parse_string("hello world")
        assert result == ["hello", " world"]
    
    def test_and_mismatch(self):
        lit1 = pp.Literal("hello")
        lit2 = pp.Literal(" world")
        combined = lit1 + lit2
        with pytest.raises(ValueError):
            combined.parse_string("hello there")

class TestMatchFirst:
    def test_match_first_first_wins(self):
        lit1 = pp.Literal("hello")
        lit2 = pp.Literal("goodbye")
        combined = lit1 | lit2
        result = combined.parse_string("hello")
        assert result == ["hello"]
    
    def test_match_first_second(self):
        lit1 = pp.Literal("hello")
        lit2 = pp.Literal("goodbye")
        combined = lit1 | lit2
        result = combined.parse_string("goodbye")
        assert result == ["goodbye"]

class TestZeroOrMore:
    def test_zero_or_more_multiple(self):
        lit = pp.Literal("a")
        many = pp.ZeroOrMore(lit)
        result = many.parse_string("aaaa")
        assert result == ["a", "a", "a", "a"]
    
    def test_zero_or_more_zero(self):
        lit = pp.Literal("a")
        many = pp.ZeroOrMore(lit)
        result = many.parse_string("bbbb")
        assert result == []

class TestOneOrMore:
    def test_one_or_more_multiple(self):
        lit = pp.Literal("a")
        many = pp.OneOrMore(lit)
        result = many.parse_string("aaaa")
        assert result == ["a", "a", "a", "a"]
    
    def test_one_or_more_zero_fails(self):
        lit = pp.Literal("a")
        many = pp.OneOrMore(lit)
        with pytest.raises(ValueError):
            many.parse_string("bbbb")

class TestOptional:
    def test_optional_present(self):
        lit = pp.Literal("a")
        opt = pp.Optional(lit)
        result = opt.parse_string("a")
        assert result == ["a"]
    
    def test_optional_absent(self):
        lit = pp.Literal("a")
        opt = pp.Optional(lit)
        result = opt.parse_string("b")
        assert result == []

class TestSuppress:
    def test_suppress_no_output(self):
        lit = pp.Literal("hello")
        sup = pp.Suppress(lit)
        result = sup.parse_string("hello")
        assert result == []

class TestForward:
    def test_forward_basic(self):
        fwd = pp.Forward()
        fwd.set(pp.Literal("hello"))
        result = fwd.parse_string("hello world")
        assert result == ["hello"]

    def test_forward_ilshift(self):
        fwd = pp.Forward()
        fwd <<= pp.Word(pp.alphas())
        result = fwd.parse_string("hello world")
        assert result == ["hello"]

    def test_forward_in_combination(self):
        fwd = pp.Forward()
        fwd.set(pp.Literal("hello"))
        expr = fwd + pp.Literal(" world")
        result = expr.parse_string("hello world")
        assert result == ["hello", " world"]

    def test_forward_matches(self):
        fwd = pp.Forward()
        fwd.set(pp.Literal("hello"))
        assert fwd.matches("hello world")
        assert not fwd.matches("goodbye")

    def test_forward_search(self):
        fwd = pp.Forward()
        fwd.set(pp.Literal("hello"))
        count = fwd.search_string_count("hello world hello again")
        assert count == 2

    def test_forward_uninitialized(self):
        fwd = pp.Forward()
        with pytest.raises(ValueError):
            fwd.parse_string("hello")

    def test_forward_parse_batch(self):
        fwd = pp.Forward()
        fwd.set(pp.Literal("hello"))
        result = fwd.parse_batch(["hello", "hello", "goodbye"])
        assert result[0] == ["hello"]
        assert result[1] == ["hello"]
        assert result[2] == []

    def test_forward_transform(self):
        fwd = pp.Forward()
        fwd.set(pp.Literal("hello"))
        result = fwd.transform_string("hello world hello", "hi")
        assert result == "hi world hi"

class TestCombine:
    def test_combine_basic(self):
        word = pp.Word(pp.alphas())
        dash = pp.Literal("-")
        expr = pp.Combine(word + dash + word)
        result = expr.parse_string("hello-world")
        assert result == ["hello-world"]

    def test_combine_no_split(self):
        expr = pp.Combine(pp.Literal("abc") + pp.Literal("def"))
        result = expr.parse_string("abcdef")
        assert result == ["abcdef"]

    def test_combine_mismatch(self):
        expr = pp.Combine(pp.Literal("abc") + pp.Literal("def"))
        with pytest.raises(ValueError):
            expr.parse_string("abcxyz")

    def test_combine_in_sequence(self):
        combined = pp.Combine(pp.Word(pp.alphas()) + pp.Literal("-") + pp.Word(pp.nums()))
        rest = pp.Literal(" end")
        expr = combined + rest
        result = expr.parse_string("abc-123 end")
        assert result == ["abc-123", " end"]

    def test_combine_search(self):
        expr = pp.Combine(pp.Word(pp.alphas()) + pp.Literal("-") + pp.Word(pp.nums()))
        count = expr.search_string_count("foo-1 bar-2 baz-3")
        assert count == 3

class TestExactly:
    def test_exactly_match(self):
        lit = pp.Literal("a")
        expr = pp.Exactly(lit, 3)
        result = expr.parse_string("aaa")
        assert result == ["a", "a", "a"]

    def test_exactly_too_few(self):
        lit = pp.Literal("a")
        expr = pp.Exactly(lit, 3)
        with pytest.raises(ValueError):
            expr.parse_string("aa")

    def test_exactly_extra_ignored(self):
        lit = pp.Literal("a")
        expr = pp.Exactly(lit, 2)
        result = expr.parse_string("aaaa")
        assert result == ["a", "a"]

    def test_exactly_one(self):
        word = pp.Word(pp.alphas())
        expr = pp.Exactly(word, 1)
        result = expr.parse_string("hello")
        assert result == ["hello"]

    def test_exactly_search(self):
        lit = pp.Literal("a")
        expr = pp.Exactly(lit, 3)
        count = expr.search_string_count("aaabaaabaa")
        assert count == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
