#!/usr/bin/env python3
"""File-based Batch Processing - Bypass Python String Overhead"""

import os
import time
import tempfile

import pyparsing_rs as pp_rs
import pyparsing as pp_orig


def create_test_file(num_lines, filename="test_data.txt"):
    """Create a test file with sample data"""
    print(f"Creating test file with {num_lines:,} lines...")
    
    with open(filename, 'w') as f:
        for i in range(num_lines):
            if i % 100 == 0:
                f.write(f"TARGET_LINE_{i}\n")
            else:
                f.write(f"other_data_{i}_some_more_text_here\n")
    
    size_mb = os.path.getsize(filename) / (1024 * 1024)
    print(f"  Created: {filename} ({size_mb:.1f} MB)")
    return filename


def benchmark_file_processing():
    """Process file directly in Rust vs Python"""
    print("\n" + "="*70)
    print("FILE PROCESSING - 5 Million Lines")
    print("="*70)
    
    n = 5_000_000
    filename = create_test_file(n)
    pattern = "TARGET_LINE"
    
    try:
        # Python version - read file and process
        print("\nPython (file read + pyparsing):")
        start = time.perf_counter()
        
        pp_lit = pp_orig.Literal(pattern)
        total = 0
        matches = 0
        
        with open(filename, 'r') as f:
            for line in f:
                total += 1
                try:
                    pp_lit.parseString(line.strip(), parseAll=False)
                    matches += 1
                except:
                    pass
        
        py_time = time.perf_counter() - start
        py_throughput = n / py_time / 1000
        print(f"  Time: {py_time*1000:.2f}ms ({py_throughput:.1f}K lines/sec)")
        print(f"  Lines: {total}, Matches: {matches}")
        
        # Rust version - process file directly
        print("\nRust (file processed in Rust):")
        start = time.perf_counter()
        
        total_rust, matches_rust = pp_rs.process_file_lines(filename, pattern)
        
        rust_time = time.perf_counter() - start
        rust_throughput = n / rust_time / 1000
        speedup = py_time / rust_time
        
        print(f"  Time: {rust_time*1000:.2f}ms ({rust_throughput:.1f}K lines/sec)")
        print(f"  Lines: {total_rust}, Matches: {matches_rust}")
        print(f"  Speedup: {speedup:.1f}x")
        
        return speedup
        
    finally:
        os.remove(filename)


def benchmark_mmap_scan():
    """Memory-mapped file scan"""
    print("\n" + "="*70)
    print("MEMORY-MAPPED FILE SCAN - 10 Million Lines")
    print("="*70)
    
    n = 10_000_000
    filename = create_test_file(n, "large_file.txt")
    pattern = "TARGET_LINE"
    
    try:
        # Python version
        print("\nPython (line-by-line):")
        start = time.perf_counter()
        
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                if pattern in line:
                    count += 1
        
        py_time = time.perf_counter() - start
        py_throughput = n / py_time / 1000
        print(f"  Time: {py_time*1000:.2f}ms ({py_throughput:.1f}K lines/sec)")
        print(f"  Matches: {count}")
        
        # Rust mmap version
        print("\nRust (memory-mapped):")
        start = time.perf_counter()
        
        count_rust = pp_rs.mmap_file_scan(filename, pattern)
        
        rust_time = time.perf_counter() - start
        rust_throughput = n / rust_time / 1000
        speedup = py_time / rust_time
        
        print(f"  Time: {rust_time*1000:.2f}ms ({rust_throughput:.1f}K lines/sec)")
        print(f"  Matches: {count_rust}")
        print(f"  Speedup: {speedup:.1f}x")
        
        return speedup
        
    finally:
        os.remove(filename)


def benchmark_grep():
    """Grep-like pattern matching"""
    print("\n" + "="*70)
    print("GREP-LIKE MATCHING - Return matching lines")
    print("="*70)
    
    n = 1_000_000
    filename = create_test_file(n, "grep_test.txt")
    pattern = "TARGET_LINE"
    
    try:
        # Python
        print("\nPython (read + grep):")
        start = time.perf_counter()
        
        results = []
        with open(filename, 'r') as f:
            for line in f:
                if pattern in line:
                    results.append(line.strip())
                    if len(results) >= 1000:
                        break
        
        py_time = time.perf_counter() - start
        print(f"  Time: {py_time*1000:.2f}ms")
        print(f"  Results: {len(results)}")
        
        # Rust
        print("\nRust (file_grep):")
        start = time.perf_counter()
        
        results = pp_rs.file_grep(filename, pattern, 1000)
        
        rust_time = time.perf_counter() - start
        speedup = py_time / rust_time
        
        print(f"  Time: {rust_time*1000:.2f}ms")
        print(f"  Results: {len(results)}")
        print(f"  Speedup: {speedup:.1f}x")
        
        return speedup
        
    finally:
        os.remove(filename)


def benchmark_scaling():
    """Test different file sizes"""
    print("\n" + "="*70)
    print("SCALING WITH FILE SIZE")
    print("="*70)
    
    sizes = [100000, 500000, 1000000, 5000000]
    pattern = "TARGET_LINE"
    
    print(f"{'Lines':>12} | {'Python':>10} | {'Rust':>10} | {'Speedup':>8}")
    print("-" * 50)
    
    for n in sizes:
        filename = create_test_file(n, f"scale_{n}.txt")
        
        try:
            # Python
            pp_lit = pp_orig.Literal(pattern)
            start = time.perf_counter()
            count = 0
            with open(filename, 'r') as f:
                for line in f:
                    try:
                        pp_lit.parseString(line.strip(), parseAll=False)
                        count += 1
                    except:
                        pass
            py_time = time.perf_counter() - start
            
            # Rust
            start = time.perf_counter()
            _, count_rust = pp_rs.process_file_lines(filename, pattern)
            rust_time = time.perf_counter() - start
            
            speedup = py_time / rust_time
            status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️"
            print(f"{status} {n:>11,} | {py_time*1000:>9.2f}ms | {rust_time*1000:>9.2f}ms | {speedup:>7.1f}x")
            
        finally:
            os.remove(filename)


if __name__ == "__main__":
    print("="*70)
    print("FILE-BASED PROCESSING FOR 100X SPEEDUP")
    print("="*70)
    print("\nKey advantage: No Python string creation overhead!")
    print("Data stays in Rust until results are returned.")
    
    results = []
    
    results.append(("File Processing (5M)", benchmark_file_processing()))
    results.append(("Mmap Scan (10M)", benchmark_mmap_scan()))
    results.append(("Grep (1M)", benchmark_grep()))
    
    benchmark_scaling()
    
    # Summary
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    for name, speedup in results:
        if speedup:
            status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️"
            print(f"{status} {name:.<40} {speedup:>6.1f}x")
    
    valid_results = [s for _, s in results if s is not None]
    if valid_results:
        max_speedup = max(valid_results)
        print(f"\nMaximum speedup: {max_speedup:.1f}x")
        
        if max_speedup >= 100:
            print("\n🎉🎉🎉 100X ACHIEVED! 🎉🎉🎉")
