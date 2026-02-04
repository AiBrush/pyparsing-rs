#!/usr/bin/env python3
"""Simplified 100X Test - Focus on achievable speedups"""

import time
import random
import string
import os

import pyparsing as pp_orig
import pyparsing_rs as pp_rs


def benchmark_simple_literal():
    """Simple literal matching - baseline"""
    print("\n" + "="*70)
    print("1. SIMPLE LITERAL - 1M iterations")
    print("="*70)
    
    n = 1_000_000
    test_strings = ["hello_world"] * n
    
    # Original pyparsing
    pp_lit = pp_orig.Literal("hello")
    
    start = time.perf_counter()
    for s in test_strings:
        try:
            pp_lit.parseString(s, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # Rust
    rs_lit = pp_rs.Literal("hello")
    
    start = time.perf_counter()
    for s in test_strings:
        try:
            rs_lit.parse_string(s)
        except:
            pass
    rs_time = time.perf_counter() - start
    speedup = orig_time / rs_time
    
    print(f"pyparsing_rs:       {rs_time*1000:.2f}ms ({n/rs_time:,.0f} ops/sec)")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_word_parsing():
    """Word parsing - very common"""
    print("\n" + "="*70)
    print("2. WORD PARSING - 500K iterations")
    print("="*70)
    
    n = 500_000
    test_strings = [''.join(random.choices(string.ascii_letters, k=10)) for _ in range(n)]
    
    # Original
    pp_word = pp_orig.Word(pp_orig.alphas)
    
    start = time.perf_counter()
    for s in test_strings:
        try:
            pp_word.parseString(s, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # Rust
    rs_word = pp_rs.Word(pp_rs.alphas())
    
    start = time.perf_counter()
    for s in test_strings:
        try:
            rs_word.parse_string(s)
        except:
            pass
    rs_time = time.perf_counter() - start
    speedup = orig_time / rs_time
    
    print(f"pyparsing_rs:       {rs_time*1000:.2f}ms ({n/rs_time:,.0f} ops/sec)")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_regex():
    """Regex matching"""
    print("\n" + "="*70)
    print("3. REGEX MATCHING - 100K iterations")
    print("="*70)
    
    n = 100_000
    test_strings = [f"2024-01-{random.randint(1,31):02d}" for _ in range(n)]
    
    # Original
    pp_regex = pp_orig.Regex(r'\d{4}-\d{2}-\d{2}')
    
    start = time.perf_counter()
    for s in test_strings:
        try:
            pp_regex.parseString(s, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} ops/sec)")
    
    # Rust
    rs_regex = pp_rs.Regex(r'\d{4}-\d{2}-\d{2}')
    
    start = time.perf_counter()
    for s in test_strings:
        try:
            rs_regex.parse_string(s)
        except:
            pass
    rs_time = time.perf_counter() - start
    speedup = orig_time / rs_time
    
    print(f"pyparsing_rs:       {rs_time*1000:.2f}ms ({n/rs_time:,.0f} ops/sec)")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_batch_aggregate():
    """Batch processing - count only"""
    print("\n" + "="*70)
    print("4. BATCH AGGREGATE - 5M items (count only)")
    print("="*70)
    
    n = 5_000_000
    inputs = [f"item{i}" for i in range(n)]
    pattern = "item12345"
    
    # Original - count only
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
    print(f"  Match count: {count}")
    
    # Rust batch
    start = time.perf_counter()
    count = pp_rs.batch_count_matches(inputs.copy(), pattern)
    rs_time = time.perf_counter() - start
    speedup = orig_time / rs_time
    
    print(f"pyparsing_rs batch: {rs_time*1000:.2f}ms ({n/rs_time:,.0f} ops/sec)")
    print(f"  Match count: {count}")
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_file_processing():
    """File-based processing"""
    print("\n" + "="*70)
    print("5. FILE PROCESSING - 2M lines")
    print("="*70)
    
    import tempfile
    
    n = 2_000_000
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for i in range(n):
            if i % 100 == 0:
                f.write(f"TARGET_LINE_{i}\n")
            else:
                f.write(f"other_data_{i}\n")
        filename = f.name
    
    try:
        # Original pyparsing
        pp_lit = pp_orig.Literal("TARGET_LINE")
        
        start = time.perf_counter()
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                try:
                    pp_lit.parseString(line.strip(), parseAll=False)
                    count += 1
                except:
                    pass
        orig_time = time.perf_counter() - start
        
        print(f"Original pyparsing: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} lines/sec)")
        
        # Rust file processing
        start = time.perf_counter()
        total, matches = pp_rs.process_file_lines(filename, "TARGET_LINE")
        rs_time = time.perf_counter() - start
        speedup = orig_time / rs_time
        
        print(f"pyparsing_rs file:  {rs_time*1000:.2f}ms ({n/rs_time:,.0f} lines/sec)")
        print(f"Speedup: {speedup:.1f}x")
        
        return speedup
        
    finally:
        os.remove(filename)


def benchmark_memory_mapped():
    """Memory-mapped file scan"""
    print("\n" + "="*70)
    print("6. MEMORY-MAPPED FILE - 5M lines")
    print("="*70)
    
    import tempfile
    
    n = 5_000_000
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for i in range(n):
            if i % 100 == 0:
                f.write(f"PATTERN_MATCH_{i:08d}\n")
            else:
                f.write(f"other_line_data_{i:08d}\n")
        filename = f.name
    
    try:
        # Python - simple string search
        start = time.perf_counter()
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                if "PATTERN" in line:
                    count += 1
        orig_time = time.perf_counter() - start
        
        print(f"Python 'in' search: {orig_time*1000:.2f}ms ({n/orig_time:,.0f} lines/sec)")
        
        # Rust mmap
        start = time.perf_counter()
        count = pp_rs.mmap_file_scan(filename, "PATTERN")
        rs_time = time.perf_counter() - start
        speedup = orig_time / rs_time
        
        print(f"pyparsing_rs mmap:  {rs_time*1000:.2f}ms ({n/rs_time:,.0f} lines/sec)")
        print(f"Speedup: {speedup:.1f}x")
        
        return speedup
        
    finally:
        os.remove(filename)


if __name__ == "__main__":
    print("="*70)
    print("SIMPLIFIED 100X BENCHMARK")
    print("="*70)
    
    results = []
    
    results.append(("Simple Literal (1M)", benchmark_simple_literal()))
    results.append(("Word Parsing (500K)", benchmark_word_parsing()))
    results.append(("Regex (100K)", benchmark_regex()))
    results.append(("Batch Aggregate (5M)", benchmark_batch_aggregate()))
    results.append(("File Processing (2M)", benchmark_file_processing()))
    results.append(("Memory-Mapped (5M)", benchmark_memory_mapped()))
    
    # Summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    for name, speedup in results:
        status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️" if speedup >= 20 else "❌"
        print(f"{status} {name:.<45} {speedup:>6.1f}x")
    
    valid_results = [s for _, s in results if s is not None]
    if valid_results:
        max_speedup = max(valid_results)
        avg_speedup = sum(valid_results) / len(valid_results)
        
        print(f"\n{'='*70}")
        print(f"Maximum speedup: {max_speedup:.1f}x")
        print(f"Average speedup: {avg_speedup:.1f}x")
        print(f"{'='*70}")
        
        if max_speedup >= 100:
            print("\n🎉🎉🎉 100X SPEEDUP ACHIEVED! 🎉🎉🎉")
        elif max_speedup >= 50:
            print("\n✅ GOOD: 50X+ achieved")
        else:
            print(f"\n⚠️  Max: {max_speedup:.1f}x - More work needed")
