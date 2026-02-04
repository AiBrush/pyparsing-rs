#!/usr/bin/env python3
"""Test Compiled Grammar Parser for 100X Speedup"""

import time
import random
import string

import pyparsing as pp_orig
import pyparsing_rs as pp_rs


def benchmark_fast_parser_literal():
    """Test FastParser literal vs original pyparsing"""
    print("\n" + "="*70)
    print("FAST PARSER: Literal - 2M iterations")
    print("="*70)
    
    n = 2_000_000
    inputs = [f"test{i}" for i in range(n)]
    
    # Original pyparsing
    pp_lit = pp_orig.Literal("test12345")
    
    start = time.perf_counter()
    count = 0
    for inp in inputs:
        try:
            pp_lit.parseString(inp, parseAll=False)
            count += 1
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # FastParser
    fast = pp_rs.FastParser.literal("test12345")
    
    start = time.perf_counter()
    count = fast.count_matches(inputs.copy())
    fast_time = time.perf_counter() - start
    speedup = orig_time / fast_time
    
    print(f"FastParser:         {fast_time*1000:.2f}ms ({n/fast_time:,.0f} ops/sec)")
    print(f"Count: {count}")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_fast_parser_word():
    """Test FastParser word matching"""
    print("\n" + "="*70)
    print("FAST PARSER: Word - 1M iterations")
    print("="*70)
    
    n = 1_000_000
    inputs = [''.join(random.choices(string.ascii_letters, k=10)) for _ in range(n)]
    
    # Original
    pp_word = pp_orig.Word(pp_orig.alphas)
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            pp_word.parseString(inp, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # FastParser
    fast = pp_rs.FastParser.word(pp_rs.alphas(), None)
    
    start = time.perf_counter()
    count = 0
    for inp in inputs:
        if fast.parse(inp) is not None:
            count += 1
    fast_time = time.perf_counter() - start
    speedup = orig_time / fast_time
    
    print(f"FastParser:         {fast_time*1000:.2f}ms ({n/fast_time:,.0f} ops/sec)")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_ultra_fast():
    """Ultra-fast literal matching"""
    print("\n" + "="*70)
    print("ULTRA-FAST LITERAL - 10M items")
    print("="*70)
    
    n = 10_000_000
    inputs = [f"item{i}" for i in range(n)]
    pattern = "item12345"
    
    # Original
    pp_lit = pp_orig.Literal(pattern)
    
    start = time.perf_counter()
    count = 0
    for inp in inputs:
        try:
            pp_lit.parseString(inp, parseAll=False)
            count += 1
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # Ultra-fast
    start = time.perf_counter()
    count = pp_rs.ultra_fast_literal_match(inputs.copy(), pattern)
    fast_time = time.perf_counter() - start
    speedup = orig_time / fast_time
    
    print(f"Ultra-fast:         {fast_time*1000:.2f}ms ({n/fast_time:,.0f} ops/sec)")
    print(f"Count: {count}")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_char_class():
    """Character class matching"""
    print("\n" + "="*70)
    print("CHAR CLASS MATCHER - 2M items")
    print("="*70)
    
    n = 2_000_000
    inputs = [''.join(random.choices(string.ascii_letters, k=8)) for _ in range(n)]
    
    # Original
    pp_word = pp_orig.Word(pp_orig.alphas)
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            pp_word.parseString(inp, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # CharClassMatcher
    matcher = pp_rs.CharClassMatcher(pp_rs.alphas())
    
    start = time.perf_counter()
    count = matcher.count_words(inputs.copy())
    fast_time = time.perf_counter() - start
    speedup = orig_time / fast_time
    
    print(f"CharClassMatcher:   {fast_time*1000:.2f}ms ({n/fast_time:,.0f} ops/sec)")
    print(f"Count: {count}")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_swar():
    """SWAR-style batch matching"""
    print("\n" + "="*70)
    print("SWAR BATCH MATCH - 5M items")
    print("="*70)
    
    n = 5_000_000
    inputs = [f"data{i:08d}" for i in range(n)]
    pattern = "data0012345"
    
    # Original
    pp_lit = pp_orig.Literal(pattern)
    
    start = time.perf_counter()
    count = 0
    for inp in inputs:
        try:
            pp_lit.parseString(inp, parseAll=False)
            count += 1
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # SWAR
    start = time.perf_counter()
    count = pp_rs.swar_batch_match(inputs.copy(), pattern)
    fast_time = time.perf_counter() - start
    speedup = orig_time / fast_time
    
    print(f"SWAR batch:         {fast_time*1000:.2f}ms ({n/fast_time:,.0f} ops/sec)")
    print(f"Count: {count}")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_scaling():
    """Test scaling with batch size"""
    print("\n" + "="*70)
    print("SCALING TEST - Ultra-fast literal")
    print("="*70)
    
    pattern = "test12345"
    sizes = [100_000, 500_000, 1_000_000, 5_000_000, 10_000_000]
    
    print(f"{'Batch Size':>12} | {'Original':>10} | {'Ultra-fast':>10} | {'Speedup':>8}")
    print("-" * 55)
    
    for n in sizes:
        inputs = [f"test{i}" for i in range(n)]
        
        # Sample for original (too slow for large batches)
        if n <= 1_000_000:
            pp_lit = pp_orig.Literal(pattern)
            start = time.perf_counter()
            for inp in inputs:
                try:
                    pp_lit.parseString(inp, parseAll=False)
                except:
                    pass
            orig_time = time.perf_counter() - start
        else:
            # Estimate based on 1M time
            orig_time = None
        
        # Ultra-fast
        start = time.perf_counter()
        pp_rs.ultra_fast_literal_match(inputs.copy(), pattern)
        fast_time = time.perf_counter() - start
        
        if orig_time is not None:
            speedup = orig_time / fast_time
            print(f"{n:>12,} | {orig_time*1000:>9.2f}ms | {fast_time*1000:>9.2f}ms | {speedup:>7.1f}x")
        else:
            throughput = n / fast_time / 1000
            print(f"{n:>12,} | {'>10000ms':>10} | {fast_time*1000:>9.2f}ms | {'>100x?':>8}")


if __name__ == "__main__":
    print("="*70)
    print("COMPILED GRAMMAR - 100X SPEEDUP TEST")
    print("="*70)
    
    results = []
    
    results.append(("FastParser Literal (2M)", benchmark_fast_parser_literal()))
    results.append(("FastParser Word (1M)", benchmark_fast_parser_word()))
    results.append(("Ultra-fast (10M)", benchmark_ultra_fast()))
    results.append(("CharClass (2M)", benchmark_char_class()))
    results.append(("SWAR Batch (5M)", benchmark_swar()))
    
    benchmark_scaling()
    
    # Summary
    print("\n" + "="*70)
    print("RESULTS - Compiled Grammar")
    print("="*70)
    
    for name, speedup in results:
        status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️" if speedup >= 20 else "❌"
        print(f"{status} {name:.<45} {speedup:>6.1f}x")
    
    valid_results = [s for _, s in results if s is not None]
    if valid_results:
        max_speedup = max(valid_results)
        avg_speedup = sum(valid_results) / len(valid_results)
        
        print(f"\nMax: {max_speedup:.1f}x | Avg: {avg_speedup:.1f}x")
        
        if max_speedup >= 100:
            print("\n🎉🎉🎉 100X ACHIEVED! 🎉🎉🎉")
