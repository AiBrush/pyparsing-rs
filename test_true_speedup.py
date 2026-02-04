#!/usr/bin/env python3
"""TRUE Speedup - Compare Rust vs Fastest Python (not pyparsing)"""

import os
import time
import tempfile
import re

import pyparsing_rs as pp_rs


def create_test_file(num_lines, filename="test.txt"):
    """Create test file"""
    with open(filename, 'w') as f:
        for i in range(num_lines):
            if i % 100 == 0:
                f.write(f"TARGET_{i:08d}_MATCH\n")
            else:
                f.write(f"other_line_{i}_with_some_data\n")
    return filename


def benchmark_true_comparison():
    """Compare Rust vs fastest Python approaches"""
    print("="*70)
    print("TRUE SPEEDUP: Rust vs Fastest Python")
    print("="*70)
    
    n = 5_000_000
    filename = create_test_file(n)
    pattern = "TARGET"
    
    try:
        print(f"\nFile: {n:,} lines ({os.path.getsize(filename)/(1024*1024):.1f} MB)")
        print(f"Pattern: '{pattern}'")
        
        # 1. Python - simple 'in' operator (FASTEST)
        print("\n" + "-"*70)
        print("1. Python 'in' operator (absolute fastest):")
        start = time.perf_counter()
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                if pattern in line:
                    count += 1
        py_in_time = time.perf_counter() - start
        print(f"   Time: {py_in_time*1000:.2f}ms")
        print(f"   Matches: {count}")
        
        # 2. Python - regex
        print("\n2. Python regex:")
        regex = re.compile(pattern)
        start = time.perf_counter()
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                if regex.search(line):
                    count += 1
        py_regex_time = time.perf_counter() - start
        print(f"   Time: {py_regex_time*1000:.2f}ms")
        print(f"   Matches: {count}")
        
        # 3. Python - str.startswith
        print("\n3. Python str.startswith:")
        start = time.perf_counter()
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith(pattern):
                    count += 1
        py_start_time = time.perf_counter() - start
        print(f"   Time: {py_start_time*1000:.2f}ms")
        print(f"   Matches: {count}")
        
        # 4. Rust - file_lines
        print("\n4. Rust file_lines:")
        start = time.perf_counter()
        total, matches = pp_rs.process_file_lines(filename, pattern)
        rust_time = time.perf_counter() - start
        print(f"   Time: {rust_time*1000:.2f}ms")
        print(f"   Lines: {total}, Matches: {matches}")
        
        # 5. Rust - mmap
        print("\n5. Rust memory-mapped:")
        start = time.perf_counter()
        count = pp_rs.mmap_file_scan(filename, pattern)
        rust_mmap_time = time.perf_counter() - start
        print(f"   Time: {rust_mmap_time*1000:.2f}ms")
        print(f"   Matches: {count}")
        
        # Summary
        print("\n" + "="*70)
        print("SPEEDUP SUMMARY")
        print("="*70)
        
        baseline = py_in_time
        
        print(f"\nvs Python 'in' (fastest possible):")
        print(f"  Rust file_lines: {baseline/rust_time:.1f}x")
        print(f"  Rust mmap:       {baseline/rust_mmap_time:.1f}x")
        
        print(f"\nvs Python regex:")
        print(f"  Rust file_lines: {py_regex_time/rust_time:.1f}x")
        print(f"  Rust mmap:       {py_regex_time/rust_mmap_time:.1f}x")
        
        # Throughput comparison
        print("\n" + "="*70)
        print("THROUGHPUT COMPARISON")
        print("="*70)
        
        print(f"\nPython 'in':      {n/py_in_time/1000:.1f}K lines/sec")
        print(f"Python regex:     {n/py_regex_time/1000:.1f}K lines/sec")
        print(f"Rust file_lines:  {n/rust_time/1000:.1f}K lines/sec")
        print(f"Rust mmap:        {n/rust_mmap_time/1000:.1f}K lines/sec")
        
        max_speedup = max(baseline/rust_time, baseline/rust_mmap_time)
        print(f"\n{'='*70}")
        if max_speedup >= 100:
            print(f"🎉 MAX SPEEDUP: {max_speedup:.1f}x - GOAL ACHIEVED!")
        else:
            print(f"⚠️  MAX SPEEDUP: {max_speedup:.1f}x - Need more optimization")
        print(f"{'='*70}")
        
        return max_speedup
        
    finally:
        os.remove(filename)


def benchmark_string_batch():
    """Compare with strings in memory"""
    print("\n" + "="*70)
    print("IN-MEMORY STRING PROCESSING")
    print("="*70)
    
    n = 2_000_000
    inputs = []
    for i in range(n):
        if i % 100 == 0:
            inputs.append(f"TARGET_{i:08d}_MATCH")
        else:
            inputs.append(f"other_data_{i}")
    
    pattern = "TARGET"
    
    print(f"\nDataset: {n:,} strings in memory")
    
    # Python 'in' operator
    print("\nPython 'in' operator:")
    start = time.perf_counter()
    count = sum(1 for s in inputs if pattern in s)
    py_time = time.perf_counter() - start
    print(f"  Time: {py_time*1000:.2f}ms, Count: {count}")
    
    # Python list comprehension with startswith
    print("\nPython str.startswith:")
    start = time.perf_counter()
    count = sum(1 for s in inputs if s.startswith(pattern))
    py_start_time = time.perf_counter() - start
    print(f"  Time: {py_start_time*1000:.2f}ms, Count: {count}")
    
    # Rust aggregate stats
    print("\nRust aggregate_stats:")
    start = time.perf_counter()
    matches, total, _ = pp_rs.aggregate_stats(inputs.copy(), pattern)
    rust_time = time.perf_counter() - start
    print(f"  Time: {rust_time*1000:.2f}ms, Count: {matches}")
    
    # Rust parallel count
    print("\nRust batch_count_matches (parallel):")
    start = time.perf_counter()
    count = pp_rs.batch_count_matches(inputs.copy(), pattern)
    rust_par_time = time.perf_counter() - start
    print(f"  Time: {rust_par_time*1000:.2f}ms, Count: {count}")
    
    print("\n" + "-"*70)
    speedup1 = py_time / rust_time
    speedup2 = py_time / rust_par_time
    print(f"Speedup vs Python 'in': {speedup1:.1f}x (aggregate), {speedup2:.1f}x (parallel)")
    
    return max(speedup1, speedup2)


def benchmark_large_batch():
    """Test with very large batches"""
    print("\n" + "="*70)
    print("LARGE BATCH TEST - 10 Million strings")
    print("="*70)
    
    n = 10_000_000
    inputs = [f"item{i}" for i in range(n)]
    pattern = "item12345"
    
    print(f"\nDataset: {n:,} strings")
    
    # Python
    print("\nPython 'in' operator:")
    start = time.perf_counter()
    count = sum(1 for s in inputs if pattern in s)
    py_time = time.perf_counter() - start
    py_throughput = n / py_time / 1000
    print(f"  Time: {py_time*1000:.2f}ms ({py_throughput:.1f}K ops/sec)")
    
    # Rust
    print("\nRust batch_count_matches:")
    start = time.perf_counter()
    count = pp_rs.batch_count_matches(inputs.copy(), pattern)
    rust_time = time.perf_counter() - start
    rust_throughput = n / rust_time / 1000
    speedup = py_time / rust_time
    print(f"  Time: {rust_time*1000:.2f}ms ({rust_throughput:.1f}K ops/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TRUE SPEEDUP ANALYSIS")
    print("Comparing Rust against fastest possible Python")
    print("="*70)
    
    results = []
    
    results.append(("File Processing", benchmark_true_comparison()))
    results.append(("In-Memory Batch", benchmark_string_batch()))
    results.append(("Large Batch (10M)", benchmark_large_batch()))
    
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    for name, speedup in results:
        status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️" if speedup >= 20 else "❌"
        print(f"{status} {name:.<40} {speedup:>6.1f}x")
    
    max_speedup = max(results, key=lambda x: x[1])[1]
    
    print(f"\n{'='*70}")
    if max_speedup >= 100:
        print(f"🎉🎉🎉 100X SPEEDUP ACHIEVED: {max_speedup:.1f}x 🎉🎉🎉")
    else:
        print(f"Maximum speedup: {max_speedup:.1f}x")
        print("100X requires more aggressive optimization")
    print(f"{'='*70}")
