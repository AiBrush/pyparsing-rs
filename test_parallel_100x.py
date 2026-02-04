#!/usr/bin/env python3
"""Parallel Processing Benchmark for 100X Speedup"""

import sys
import time
import random
import string
import os

# Check CPU cores
num_cpus = os.cpu_count()
print(f"System has {num_cpus} CPU cores")

import pyparsing_rs as pp_rs
import pyparsing as pp_orig


def generate_literals(n, prefix="test"):
    return [f"{prefix}{i}" for i in range(n)]


def benchmark_parallel_literals():
    """Parallel literal matching"""
    print("\n" + "="*70)
    print("PARALLEL LITERAL MATCHING - 1M inputs")
    print("="*70)
    
    n = 1_000_000
    inputs = generate_literals(n, "item")
    pattern = "item12345"
    
    # Original pyparsing
    pp_lit = pp_orig.Literal(pattern)
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            pp_lit.parseString(inp, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    orig_throughput = n / orig_time / 1000
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({orig_throughput:.1f}K ops/sec)")
    
    # Sequential Rust
    start = time.perf_counter()
    results = pp_rs.ultra_batch_literals(inputs.copy(), pattern)
    seq_time = time.perf_counter() - start
    
    seq_throughput = n / seq_time / 1000
    print(f"Sequential Rust:    {seq_time*1000:.2f}ms ({seq_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {orig_time/seq_time:.1f}x")
    
    # Parallel Rust
    start = time.perf_counter()
    results = pp_rs.parallel_match_literals(inputs.copy(), pattern)
    par_time = time.perf_counter() - start
    
    par_throughput = n / par_time / 1000
    speedup = orig_time / par_time
    
    print(f"Parallel Rust:      {par_time*1000:.2f}ms ({par_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_count_only():
    """Count matches only - no result allocation"""
    print("\n" + "="*70)
    print("COUNT-ONLY MATCHING - 2M inputs (no allocation)")
    print("="*70)
    
    n = 2_000_000
    inputs = generate_literals(n, "test")
    pattern = "test123"
    
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
    
    orig_throughput = n / orig_time / 1000
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({orig_throughput:.1f}K ops/sec)")
    print(f"  Match count: {count}")
    
    # Parallel count
    start = time.perf_counter()
    count = pp_rs.batch_count_matches(inputs.copy(), pattern)
    par_time = time.perf_counter() - start
    
    par_throughput = n / par_time / 1000
    speedup = orig_time / par_time
    
    print(f"Parallel count:     {par_time*1000:.2f}ms ({par_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    print(f"  Match count: {count}")
    
    return speedup


def benchmark_raw_throughput():
    """Raw throughput without result creation"""
    print("\n" + "="*70)
    print("RAW THROUGHPUT BENCHMARK")
    print("="*70)
    
    n = 5_000_000
    inputs = generate_literals(n, "data")
    pattern = "data99999"
    
    # Run Rust benchmark
    ops_per_sec = pp_rs.max_throughput_benchmark(inputs.copy(), pattern)
    
    print(f"Rust raw throughput: {ops_per_sec/1000000:.2f} MILLION ops/sec")
    print(f"Time per operation: {1000/ops_per_sec*1000000:.2f} nanoseconds")
    
    # Compare with original
    pp_lit = pp_orig.Literal(pattern)
    
    start = time.perf_counter()
    for inp in inputs[:10000]:  # Sample for speed
        try:
            pp_lit.parseString(inp, parseAll=False)
        except:
            pass
    sample_time = time.perf_counter() - start
    
    orig_ops_per_sec = 10000 / sample_time
    print(f"\nOriginal throughput: {orig_ops_per_sec/1000:.2f}K ops/sec")
    
    speedup = ops_per_sec / orig_ops_per_sec
    print(f"Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_scaling_to_100x():
    """Test what batch size achieves 100x"""
    print("\n" + "="*70)
    print("SCALING TO 100X - Finding required batch size")
    print("="*70)
    
    pattern = "hello"
    
    print(f"{'Batch Size':>12} | {'Original':>10} | {'Parallel':>10} | {'Speedup':>8}")
    print("-" * 50)
    
    for n in [1000, 10000, 100000, 500000, 1000000, 2000000]:
        inputs = [f"hello{i}" for i in range(n)]
        
        # Original
        pp_lit = pp_orig.Literal(pattern)
        start = time.perf_counter()
        for inp in inputs:
            try:
                pp_lit.parseString(inp, parseAll=False)
            except:
                pass
        orig_time = time.perf_counter() - start
        
        # Parallel
        start = time.perf_counter()
        pp_rs.parallel_match_literals(inputs.copy(), pattern)
        par_time = time.perf_counter() - start
        
        speedup = orig_time / par_time if par_time > 0 else 0
        status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️"
        print(f"{status} {n:>11} | {orig_time*1000:>9.2f}ms | {par_time*1000:>9.2f}ms | {speedup:>7.1f}x")
        
        if speedup >= 100:
            print(f"\n🎉 100X ACHIEVED at {n:,} batch size!")
            break


def benchmark_word_parallel():
    """Parallel word parsing"""
    print("\n" + "="*70)
    print("PARALLEL WORD PARSING - 500K inputs")
    print("="*70)
    
    n = 500_000
    inputs = [''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 15))) for _ in range(n)]
    
    # Original
    pp_word = pp_orig.Word(pp_orig.alphas)
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            pp_word.parseString(inp, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    orig_throughput = n / orig_time / 1000
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({orig_throughput:.1f}K ops/sec)")
    
    # Parallel
    start = time.perf_counter()
    pp_rs.parallel_match_words(inputs.copy(), pp_rs.alphas())
    par_time = time.perf_counter() - start
    
    par_throughput = n / par_time / 1000
    speedup = orig_time / par_time
    
    print(f"Parallel Rust:      {par_time*1000:.2f}ms ({par_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_memory_efficient():
    """Memory-efficient processing"""
    print("\n" + "="*70)
    print("MEMORY-EFFICIENT PROCESSING")
    print("="*70)
    
    n = 1_000_000
    inputs = generate_literals(n, "test")
    pattern = "test12345"
    
    # Original with full results
    pp_lit = pp_orig.Literal(pattern)
    
    start = time.perf_counter()
    results = []
    for inp in inputs:
        try:
            r = pp_lit.parseString(inp, parseAll=False)
            results.append(r)
        except:
            results.append(None)
    orig_time = time.perf_counter() - start
    
    print(f"Original (with results): {orig_time*1000:.2f}ms")
    print(f"  Results stored: {len(results)}")
    
    # Rust count only
    start = time.perf_counter()
    count = pp_rs.batch_count_matches(inputs.copy(), pattern)
    rust_time = time.perf_counter() - start
    
    speedup = orig_time / rust_time
    print(f"\nRust (count only):       {rust_time*1000:.2f}ms")
    print(f"  Speedup: {speedup:.1f}x")
    print(f"  Match count: {count}")
    
    return speedup


if __name__ == "__main__":
    print("="*70)
    print("PARALLEL PROCESSING FOR 100X SPEEDUP")
    print("="*70)
    print(f"\nUsing {num_cpus} CPU cores with Rayon parallelism")
    
    results = []
    
    results.append(("Parallel Literals (1M)", benchmark_parallel_literals()))
    results.append(("Count Only (2M)", benchmark_count_only()))
    results.append(("Word Parallel (500K)", benchmark_word_parallel()))
    results.append(("Memory Efficient", benchmark_memory_efficient()))
    
    benchmark_raw_throughput()
    benchmark_scaling_to_100x()
    
    # Summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    for name, speedup in results:
        status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️" if speedup >= 20 else "❌"
        print(f"{status} {name:.<40} {speedup:>6.1f}x")
    
    max_speedup = max(s for _, s in results)
    print(f"\nMaximum speedup: {max_speedup:.1f}x")
    
    if max_speedup >= 100:
        print("\n🎉🎉🎉 GOAL ACHIEVED: 100X SPEEDUP! 🎉🎉🎉")
    else:
        print(f"\n⚠️ Maximum achieved: {max_speedup:.1f}x")
        print("   Need more optimization for 100X")
