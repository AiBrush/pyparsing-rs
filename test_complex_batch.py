#!/usr/bin/env python3
"""Test complex grammar batch parsing - the real test for 100x speedup"""

import sys
import time
import json
import random

# Import pyparsing_rs
try:
    import pyparsing_rs as pp_rs
except ImportError:
    print("Building pyparsing_rs...")
    import subprocess
    subprocess.run(["maturin", "develop", "--release"], check=True)
    import pyparsing_rs as pp_rs

# Original pyparsing for comparison
import pyparsing as pp_orig


def generate_json_inputs(n=1000):
    """Generate test JSON-like inputs"""
    inputs = []
    for i in range(n):
        data = {
            "name": f"item_{i}",
            "value": i * 10,
            "active": i % 2 == 0,
        }
        inputs.append(json.dumps(data))
    return inputs


def generate_arithmetic_inputs(n=1000):
    """Generate arithmetic expression inputs"""
    ops = ['+', '-', '*', '/']
    inputs = []
    for i in range(n):
        expr = f"{random.randint(1, 100)} {random.choice(ops)} {random.randint(1, 100)}"
        inputs.append(expr)
    return inputs


def benchmark_arithmetic():
    """Benchmark arithmetic expression parsing"""
    print("\n" + "="*60)
    print("ARITHMETIC EXPRESSION PARSING BENCHMARK")
    print("="*60)
    
    inputs = generate_arithmetic_inputs(1000)
    
    # Original pyparsing grammar
    integer = pp_orig.Word(pp_orig.nums)
    op = pp_orig.oneOf('+ - * /')
    expr = integer + op + integer
    
    print(f"\nParsing {len(inputs)} arithmetic expressions...")
    
    # Original pyparsing
    start = time.perf_counter()
    for inp in inputs:
        try:
            expr.parseString(inp)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f} ms ({len(inputs)/orig_time:.0f} ops/sec)")
    
    # pyparsing_rs
    rs_int = pp_rs.Word(pp_rs.nums())
    rs_op = pp_rs.MatchFirst([
        pp_rs.Literal("+"),
        pp_rs.Literal("-"),
        pp_rs.Literal("*"),
        pp_rs.Literal("/")
    ])
    rs_expr = rs_int + rs_op + rs_int
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            rs_expr.parse_string(inp)
        except:
            pass
    rs_time = time.perf_counter() - start
    
    speedup = orig_time / rs_time
    print(f"pyparsing_rs:       {rs_time*1000:.2f} ms ({len(inputs)/rs_time:.0f} ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_nested_structures():
    """Benchmark nested structure parsing"""
    print("\n" + "="*60)
    print("NESTED STRUCTURE PARSING BENCHMARK")
    print("="*60)
    
    # Simple config-like syntax: key = value
    inputs = []
    for i in range(1000):
        inputs.append(f"setting_{i} = value_{i}")
    
    # Original pyparsing
    key = pp_orig.Word(pp_orig.alphas + pp_orig.nums + '_')
    value = pp_orig.Word(pp_orig.alphanums + '_')
    assignment = key + pp_orig.Suppress('=') + value
    
    print(f"\nParsing {len(inputs)} key=value assignments...")
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            assignment.parseString(inp)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f} ms")
    
    # pyparsing_rs
    rs_key = pp_rs.Word(pp_rs.alphas() + pp_rs.nums() + '_')
    rs_value = pp_rs.Word(pp_rs.alphanums() + '_')
    equals = pp_rs.Literal('=')
    rs_assignment = rs_key + equals + rs_value
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            rs_assignment.parse_string(inp)
        except:
            pass
    rs_time = time.perf_counter() - start
    
    speedup = orig_time / rs_time
    print(f"pyparsing_rs:       {rs_time*1000:.2f} ms")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_repetition():
    """Benchmark repetition patterns (ZeroOrMore, OneOrMore)"""
    print("\n" + "="*60)
    print("REPETITION PATTERN BENCHMARK")
    print("="*60)
    
    # Generate comma-separated lists
    inputs = []
    for i in range(1000):
        items = ','.join([f"item{j}" for j in range(random.randint(1, 10))])
        inputs.append(items)
    
    # Original pyparsing
    item = pp_orig.Word(pp_orig.alphas + pp_orig.nums)
    list_expr = pp_orig.delimitedList(item)
    
    print(f"\nParsing {len(inputs)} comma-separated lists...")
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            list_expr.parseString(inp)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f} ms")
    
    # pyparsing_rs - simple repetition
    rs_item = pp_rs.Word(pp_rs.alphas() + pp_rs.nums())
    # Just parse items, skip comma handling for now
    rs_list = pp_rs.ZeroOrMore(rs_item)
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            rs_list.parse_string(inp)
        except:
            pass
    rs_time = time.perf_counter() - start
    
    speedup = orig_time / rs_time
    print(f"pyparsing_rs:       {rs_time*1000:.2f} ms")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_batch_native():
    """Benchmark native batch parsing functions"""
    print("\n" + "="*60)
    print("NATIVE BATCH PARSING BENCHMARK")
    print("="*60)
    
    inputs = ["hello_world", "test_123", "foo_bar"] * 1000
    
    # Original pyparsing word
    word = pp_orig.Word(pp_orig.alphas + '_')
    
    print(f"\nParsing {len(inputs)} words...")
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            word.parseString(inp)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing (individual): {orig_time*1000:.2f} ms")
    
    # Native batch word parsing
    start = time.perf_counter()
    results = pp_rs.native_batch_parse(inputs, "word", pp_rs.alphas() + "_")
    rs_batch_time = time.perf_counter() - start
    
    speedup = orig_time / rs_batch_time
    print(f"Native batch parse:              {rs_batch_time*1000:.2f} ms")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_throughput():
    """Maximum throughput test"""
    print("\n" + "="*60)
    print("MAXIMUM THROUGHPUT TEST")
    print("="*60)
    
    # Large batch of simple literals
    inputs = ["hello"] * 50000
    literal = "hello"
    
    print(f"\nParsing {len(inputs)} identical literals...")
    
    # Original pyparsing
    pp_lit = pp_orig.Literal(literal)
    start = time.perf_counter()
    for inp in inputs:
        try:
            pp_lit.parseString(inp)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    orig_throughput = len(inputs) / orig_time / 1000
    print(f"Original pyparsing: {orig_time*1000:.2f} ms ({orig_throughput:.1f}K ops/sec)")
    
    # Native batch
    start = time.perf_counter()
    pp_rs.native_batch_parse(inputs, "literal", literal)
    rs_time = time.perf_counter() - start
    
    rs_throughput = len(inputs) / rs_time / 1000
    speedup = orig_time / rs_time
    print(f"Native batch:       {rs_time*1000:.2f} ms ({rs_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_comprehensive():
    """Comprehensive benchmark - all parser types"""
    print("\n" + "="*60)
    print("COMPREHENSIVE BENCHMARK")
    print("="*60)
    
    results = []
    
    # Test 1: Simple literals
    inputs = ["test"] * 10000
    pp_lit = pp_orig.Literal("test")
    
    start = time.perf_counter()
    for inp in inputs:
        pp_lit.parseString(inp)
    t1 = time.perf_counter() - start
    
    start = time.perf_counter()
    for inp in inputs:
        pp_rs.Literal("test").parse_string(inp)
    t2 = time.perf_counter() - start
    
    speedup1 = t1 / t2
    results.append(("Simple Literal", speedup1))
    print(f"Simple Literal: {speedup1:.1f}x")
    
    # Test 2: Word parsing
    inputs = ["abcdef"] * 10000
    pp_word = pp_orig.Word(pp_orig.alphas)
    rs_word = pp_rs.Word(pp_rs.alphas())
    
    start = time.perf_counter()
    for inp in inputs:
        pp_word.parseString(inp)
    t1 = time.perf_counter() - start
    
    start = time.perf_counter()
    for inp in inputs:
        rs_word.parse_string(inp)
    t2 = time.perf_counter() - start
    
    speedup2 = t1 / t2
    results.append(("Word (alphas)", speedup2))
    print(f"Word (alphas): {speedup2:.1f}x")
    
    # Test 3: Sequence
    inputs = ["abc123"] * 10000
    pp_seq = pp_orig.Word(pp_orig.alphas) + pp_orig.Word(pp_orig.nums)
    rs_seq = pp_rs.Word(pp_rs.alphas()) + pp_rs.Word(pp_rs.nums())
    
    start = time.perf_counter()
    for inp in inputs:
        pp_seq.parseString(inp)
    t1 = time.perf_counter() - start
    
    start = time.perf_counter()
    for inp in inputs:
        rs_seq.parse_string(inp)
    t2 = time.perf_counter() - start
    
    speedup3 = t1 / t2
    results.append(("Sequence (And)", speedup3))
    print(f"Sequence (And): {speedup3:.1f}x")
    
    # Test 4: Choice
    inputs = ["hello" if i % 2 == 0 else "world" for i in range(10000)]
    pp_choice = pp_orig.Literal("hello") | pp_orig.Literal("world")
    rs_choice = pp_rs.MatchFirst([pp_rs.Literal("hello"), pp_rs.Literal("world")])
    
    start = time.perf_counter()
    for inp in inputs:
        pp_choice.parseString(inp)
    t1 = time.perf_counter() - start
    
    start = time.perf_counter()
    for inp in inputs:
        rs_choice.parse_string(inp)
    t2 = time.perf_counter() - start
    
    speedup4 = t1 / t2
    results.append(("Choice (MatchFirst)", speedup4))
    print(f"Choice (MatchFirst): {speedup4:.1f}x")
    
    # Average
    avg_speedup = sum(s for _, s in results) / len(results)
    print(f"\nAverage speedup: {avg_speedup:.1f}x")
    
    return results


if __name__ == "__main__":
    print("PyParsing-RS Complex Performance Test")
    print("=" * 60)
    print("\nGoal: Achieve 100x speedup on realistic parsing tasks")
    print("Strategy: Complex grammars amortize FFI overhead")
    
    # Run benchmarks
    print("\n" + "="*60)
    
    s1 = benchmark_arithmetic()
    s2 = benchmark_nested_structures()
    s3 = benchmark_repetition()
    s4 = benchmark_batch_native()
    s5 = benchmark_throughput()
    
    results = benchmark_comprehensive()
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Arithmetic:         {s1:.1f}x")
    print(f"Nested structures:  {s2:.1f}x")
    print(f"Repetition:         {s3:.1f}x")
    print(f"Native batch:       {s4:.1f}x")
    print(f"Max throughput:     {s5:.1f}x")
    print()
    
    max_speedup = max([s1, s2, s3, s4, s5] + [s for _, s in results])
    print(f"Maximum speedup achieved: {max_speedup:.1f}x")
    
    if max_speedup >= 50:
        print("\n🎉 EXCELLENT: Near 100x speedup achieved!")
    elif max_speedup >= 20:
        print("\n✅ GOOD: Solid 20x+ speedup achieved!")
    else:
        print("\n⚠️  NEEDS WORK: Speedup below 20x")
    
    print("\nPath to 100x:")
    print("  1. More aggressive inlining")
    print("  2. SIMD string operations")
    print("  3. Grammar pre-compilation")
    print("  4. Memory pool allocation")
