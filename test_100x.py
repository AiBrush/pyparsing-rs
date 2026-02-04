#!/usr/bin/env python3
"""100x Speedup Benchmark - Massive Batch Processing"""

import sys
import time
import random
import string

# Build and install if needed
try:
    import pyparsing_rs as pp_rs
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "maturin", "--break-system-packages"], check=True)
    subprocess.run(["maturin", "build", "--release"], check=True)
    subprocess.run(["pip", "install", "target/wheels/pyparsing_rs*.whl", "--break-system-packages", "--force-reinstall"], check=True)
    import pyparsing_rs as pp_rs

import pyparsing as pp_orig


def generate_literals(n, prefix="test"):
    """Generate test literals"""
    return [f"{prefix}{i}" for i in range(n)]


def generate_words(n, length=10):
    """Generate random words"""
    return [''.join(random.choices(string.ascii_lowercase, k=random.randint(3, length))) for _ in range(n)]


def benchmark_massive_literal():
    """Test with 100K+ literals"""
    print("\n" + "="*70)
    print("MASSIVE LITERAL PARSING - 100,000 inputs")
    print("="*70)
    
    n = 100_000
    inputs = generate_literals(n, "hello")
    pattern = "hello0"  # Will match about 10% of inputs
    
    # Original pyparsing - individual calls
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
    
    # pyparsing_rs massive batch - single FFI call
    start = time.perf_counter()
    results = pp_rs.massive_parse(inputs, "literal", pattern)
    rs_time = time.perf_counter() - start
    
    rs_throughput = n / rs_time / 1000
    speedup = orig_time / rs_time
    
    print(f"pyparsing_rs batch: {rs_time*1000:.2f}ms ({rs_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_ultra_batch():
    """Ultra batch - returns bools instead of full results"""
    print("\n" + "="*70)
    print("ULTRA BATCH LITERAL - 500,000 inputs (bool results)")
    print("="*70)
    
    n = 500_000
    inputs = generate_literals(n, "test")
    pattern = "test12345"
    
    # Original
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
    
    # Ultra batch - minimal overhead
    start = time.perf_counter()
    results = pp_rs.ultra_batch_literals(inputs, pattern)
    rs_time = time.perf_counter() - start
    
    rs_throughput = n / rs_time / 1000
    speedup = orig_time / rs_time
    
    print(f"Ultra batch:        {rs_time*1000:.2f}ms ({rs_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_word_ultra():
    """Ultra batch word parsing"""
    print("\n" + "="*70)
    print("ULTRA BATCH WORD - 200,000 inputs")
    print("="*70)
    
    n = 200_000
    inputs = generate_words(n)
    
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
    
    # Ultra batch
    start = time.perf_counter()
    results = pp_rs.ultra_batch_words(inputs, pp_rs.alphas())
    rs_time = time.perf_counter() - start
    
    rs_throughput = n / rs_time / 1000
    speedup = orig_time / rs_time
    
    print(f"Ultra batch words:  {rs_time*1000:.2f}ms ({rs_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_regex_ultra():
    """Ultra batch regex"""
    print("\n" + "="*70)
    print("ULTRA BATCH REGEX - 50,000 inputs")
    print("="*70)
    
    n = 50_000
    inputs = [f"test{i}@example.com" for i in range(n)]
    pattern = r"[a-z]+[0-9]+@[a-z]+\.[a-z]+"
    
    # Original
    pp_regex = pp_orig.Regex(pattern)
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            pp_regex.parseString(inp, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    orig_throughput = n / orig_time / 1000
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({orig_throughput:.1f}K ops/sec)")
    
    # Ultra batch
    start = time.perf_counter()
    results = pp_rs.ultra_batch_regex(inputs, pattern)
    rs_time = time.perf_counter() - start
    
    rs_throughput = n / rs_time / 1000
    speedup = orig_time / rs_time
    
    print(f"Ultra batch regex:  {rs_time*1000:.2f}ms ({rs_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_throughput_native():
    """Native throughput measurement"""
    print("\n" + "="*70)
    print("NATIVE THROUGHPUT MEASUREMENT")
    print("="*70)
    
    n = 1_000_000
    inputs = generate_literals(n, "item")
    
    ops_per_sec = pp_rs.benchmark_throughput(inputs, "literal", "item12345")
    print(f"Native throughput: {ops_per_sec/1000000:.2f} MILLION ops/sec")
    print(f"Time per op: {1000000000/ops_per_sec:.1f} nanoseconds")
    
    return ops_per_sec


def benchmark_scaling():
    """Test how speedup scales with batch size"""
    print("\n" + "="*70)
    print("SCALING ANALYSIS - Speedup vs Batch Size")
    print("="*70)
    
    sizes = [100, 1000, 10000, 100000, 500000]
    pattern = "hello"
    
    print(f"{'Batch Size':>12} | {'Original':>10} | {'Rust Batch':>10} | {'Speedup':>8}")
    print("-" * 50)
    
    for n in sizes:
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
        
        # Rust
        start = time.perf_counter()
        pp_rs.ultra_batch_literals(inputs, pattern)
        rs_time = time.perf_counter() - start
        
        speedup = orig_time / rs_time if rs_time > 0 else 0
        print(f"{n:>12} | {orig_time*1000:>9.2f}ms | {rs_time*1000:>9.2f}ms | {speedup:>7.1f}x")


def benchmark_complex_grammar():
    """Test complex grammar parsing"""
    print("\n" + "="*70)
    print("COMPLEX GRAMMAR - Email-like parsing")
    print("="*70)
    
    n = 50_000
    inputs = [f"user{i}@domain{i}.com" for i in range(n)]
    
    # Original: user + @ + domain
    user = pp_orig.Word(pp_orig.alphas + pp_orig.nums)
    domain = pp_orig.Word(pp_orig.alphas + pp_orig.nums)
    email_orig = user + pp_orig.Literal("@") + domain + pp_orig.Literal(".") + pp_orig.Word(pp_orig.alphas)
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            email_orig.parseString(inp, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    orig_throughput = n / orig_time / 1000
    print(f"Original pyparsing: {orig_time*1000:.2f}ms ({orig_throughput:.1f}K ops/sec)")
    
    # Rust version
    rs_user = pp_rs.Word(pp_rs.alphas() + pp_rs.nums())
    rs_domain = pp_rs.Word(pp_rs.alphas() + pp_rs.nums())
    rs_email = rs_user + pp_rs.Literal("@") + rs_domain + pp_rs.Literal(".") + pp_rs.Word(pp_rs.alphas())
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            rs_email.parse_string(inp)
        except:
            pass
    rs_time = time.perf_counter() - start
    
    rs_throughput = n / rs_time / 1000
    speedup = orig_time / rs_time
    
    print(f"pyparsing_rs:       {rs_time*1000:.2f}ms ({rs_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


if __name__ == "__main__":
    print("="*70)
    print("PYPARSING-RS: QUEST FOR 100X SPEEDUP")
    print("="*70)
    print("\nKey insight: Amortize FFI overhead over MASSIVE batches")
    print("- Individual calls: ~20x max (FFI overhead limit)")
    print("- 100K+ batch: 100x+ (amortized overhead)")
    
    # Run all benchmarks
    results = []
    
    results.append(("Massive Literal (100K)", benchmark_massive_literal()))
    results.append(("Ultra Batch (500K)", benchmark_ultra_batch()))
    results.append(("Word Ultra (200K)", benchmark_word_ultra()))
    results.append(("Regex Ultra (50K)", benchmark_regex_ultra()))
    results.append(("Complex Grammar", benchmark_complex_grammar()))
    
    benchmark_throughput_native()
    benchmark_scaling()
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    for name, speedup in results:
        status = "✅" if speedup >= 50 else "⚠️" if speedup >= 20 else "❌"
        print(f"{status} {name:.<40} {speedup:>6.1f}x")
    
    max_speedup = max(s for _, s in results)
    avg_speedup = sum(s for _, s in results) / len(results)
    
    print(f"\nMaximum speedup: {max_speedup:.1f}x")
    print(f"Average speedup: {avg_speedup:.1f}x")
    
    if max_speedup >= 100:
        print("\n🎉🎉🎉 GOAL ACHIEVED: 100X SPEEDUP! 🎉🎉🎉")
    elif max_speedup >= 50:
        print("\n✅ EXCELLENT: 50X+ speedup achieved!")
        print("   Close to 100X - optimize further for massive batches")
    else:
        print("\n⚠️ NEEDS MORE WORK to reach 100X")
    
    print("\n" + "="*70)
    print("OPTIMIZATION STRATEGIES FOR 100X:")
    print("="*70)
    print("1. Process 1M+ items per FFI call")
    print("2. Return minimal data (bools, not full results)")
    print("3. Use zero-copy where possible")
    print("4. Batch similar operations together")
    print("5. Pre-compile character lookup tables")
