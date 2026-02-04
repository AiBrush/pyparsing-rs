#!/usr/bin/env python3
"""Test batch parsing performance - the key to 100x speedup"""

import sys
import time
import random
import string

# Import pyparsing_rs
try:
    import pyparsing_rs as pp_rs
except ImportError:
    print("Building pyparsing_rs...")
    import subprocess
    subprocess.run(["maturin", "develop", "--release"], check=True)
    import pyparsing_rs as pp_rs

# Original pyparsing for comparison
try:
    import pyparsing as pp_orig
except ImportError:
    print("Installing pyparsing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pyparsing"], check=True)
    import pyparsing as pp_orig


def generate_test_inputs(n=10000, pattern="hello"):
    """Generate test inputs - some matching, some not"""
    inputs = []
    for i in range(n):
        if random.random() < 0.5:
            # Matching input
            inputs.append(pattern + ''.join(random.choices(string.ascii_lowercase, k=10)))
        else:
            # Non-matching input
            inputs.append(''.join(random.choices(string.ascii_lowercase, k=10)))
    return inputs


def benchmark_batch_literal():
    """Benchmark batch literal parsing"""
    print("\n" + "="*60)
    print("BATCH LITERAL PARSING BENCHMARK")
    print("="*60)
    
    # Test inputs
    inputs = generate_test_inputs(10000, "hello")
    literal = "hello"
    
    # Original pyparsing - individual calls
    pp_literal = pp_orig.Literal(literal)
    
    print(f"\nParsing {len(inputs)} inputs...")
    
    # Original pyparsing individual calls
    start = time.perf_counter()
    orig_results = []
    for inp in inputs:
        try:
            result = pp_literal.parseString(inp, parseAll=False)
            orig_results.append(list(result))
        except:
            orig_results.append([])
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing (individual): {orig_time*1000:.2f} ms")
    
    # pyparsing_rs individual calls
    rs_literal = pp_rs.Literal(literal)
    
    start = time.perf_counter()
    rs_results = []
    for inp in inputs:
        try:
            result = rs_literal.parse_string(inp)
            rs_results.append(result)
        except:
            rs_results.append([])
    rs_individual_time = time.perf_counter() - start
    
    print(f"pyparsing_rs (individual calls): {rs_individual_time*1000:.2f} ms")
    print(f"  Speedup (individual): {orig_time/rs_individual_time:.1f}x")
    
    # pyparsing_rs batch parsing - SINGLE FFI CALL!
    start = time.perf_counter()
    batch_results = pp_rs.batch_parse_literal(inputs, literal)
    rs_batch_time = time.perf_counter() - start
    
    print(f"\npyparsing_rs (batch - single FFI): {rs_batch_time*1000:.2f} ms")
    print(f"  Speedup (batch vs orig): {orig_time/rs_batch_time:.1f}x")
    print(f"  Speedup (batch vs individual): {rs_individual_time/rs_batch_time:.1f}x")
    
    # Verify results match
    orig_flat = [r[0] if r else None for r in orig_results]
    batch_flat = [r[0] if r else None for r in batch_results]
    match = orig_flat == batch_flat
    print(f"\nResults match: {match}")
    
    # Throughput
    throughput = len(inputs) / rs_batch_time / 1000  # K ops/sec
    print(f"  Throughput: {throughput:.1f}K ops/sec")
    
    return orig_time / rs_batch_time


def benchmark_compiled_parser():
    """Benchmark compiled parser batch operations"""
    print("\n" + "="*60)
    print("COMPILED PARSER BATCH BENCHMARK")
    print("="*60)
    
    inputs = generate_test_inputs(10000, "hello")
    
    # Original pyparsing
    pp_literal = pp_orig.Literal("hello")
    
    start = time.perf_counter()
    for inp in inputs:
        try:
            pp_literal.parseString(inp, parseAll=False)
        except:
            pass
    orig_time = time.perf_counter() - start
    
    print(f"Original pyparsing: {orig_time*1000:.2f} ms")
    
    # Compiled parser - batch
    compiled = pp_rs.CompiledParser("literal", "hello")
    
    start = time.perf_counter()
    compiled.parse_batch(inputs)
    compiled_time = time.perf_counter() - start
    
    print(f"CompiledParser (batch): {compiled_time*1000:.2f} ms")
    print(f"  Speedup: {orig_time/compiled_time:.1f}x")
    
    # Word parsing
    print("\n--- Word Parsing ---")
    word_inputs = []
    for i in range(10000):
        word_inputs.append(''.join(random.choices(string.ascii_letters, k=random.randint(5, 15))))
    
    pp_word = pp_orig.Word(pp_orig.alphas)
    rs_word = pp_rs.Word(pp_rs.alphas())
    
    # Original
    start = time.perf_counter()
    for inp in word_inputs:
        try:
            pp_word.parseString(inp, parseAll=False)
        except:
            pass
    orig_word_time = time.perf_counter() - start
    
    print(f"Original Word: {orig_word_time*1000:.2f} ms")
    
    # Compiled word parser
    compiled_word = pp_rs.CompiledParser("word", pp_rs.alphas())
    
    start = time.perf_counter()
    compiled_word.parse_batch(word_inputs)
    compiled_word_time = time.perf_counter() - start
    
    print(f"CompiledParser Word (batch): {compiled_word_time*1000:.2f} ms")
    print(f"  Speedup: {orig_word_time/compiled_word_time:.1f}x")
    
    return orig_time / compiled_time, orig_word_time / compiled_word_time


def benchmark_varying_sizes():
    """Benchmark with different batch sizes"""
    print("\n" + "="*60)
    print("SCALABILITY BENCHMARK (varying batch sizes)")
    print("="*60)
    
    sizes = [100, 1000, 10000, 100000]
    
    print("\nBatch Size | Original | Individual | Batch    | Speedup")
    print("-" * 60)
    
    for size in sizes:
        inputs = generate_test_inputs(size, "hello")
        
        # Original
        pp_literal = pp_orig.Literal("hello")
        start = time.perf_counter()
        for inp in inputs:
            try:
                pp_literal.parseString(inp, parseAll=False)
            except:
                pass
        orig_time = time.perf_counter() - start
        
        # Individual calls
        rs_literal = pp_rs.Literal("hello")
        start = time.perf_counter()
        for inp in inputs:
            try:
                rs_literal.parse_string(inp)
            except:
                pass
        rs_individual_time = time.perf_counter() - start
        
        # Batch
        start = time.perf_counter()
        pp_rs.batch_parse_literal(inputs, "hello")
        rs_batch_time = time.perf_counter() - start
        
        speedup = orig_time / rs_batch_time
        print(f"{size:>10} | {orig_time*1000:>8.2f} | {rs_individual_time*1000:>10.2f} | {rs_batch_time*1000:>8.2f} | {speedup:>7.1f}x")


if __name__ == "__main__":
    print("PyParsing-RS Batch Performance Test")
    print("=" * 60)
    
    # Run benchmarks
    speedup1 = benchmark_batch_literal()
    speedup2 = benchmark_compiled_parser()
    benchmark_varying_sizes()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Batch literal parsing: {speedup1:.1f}x speedup")
    print(f"\nThe key to 100x speedup:")
    print(f"  - FFI overhead is ~100-200ns per call")
    print(f"  - Batch operations amortize this overhead")
    print(f"  - 10K inputs = 1 FFI call vs 10K FFI calls")
    print(f"  - Result: Massive throughput increase!")
