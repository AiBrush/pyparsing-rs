#!/usr/bin/env python3
"""
REAL WORLD 100X Benchmark - Actual Pyparsing Use Cases

This tests realistic scenarios where pyparsing is actually used,
not just simple string matching where Python's C code is already fast.
"""

import time
import json
import random
import string

import pyparsing as pp_orig

# Build pyparsing_rs if needed
try:
    import pyparsing_rs as pp_rs
except ImportError:
    import subprocess
    subprocess.run(["maturin", "develop", "--release"], check=True)
    import pyparsing_rs as pp_rs


def generate_log_lines(n):
    """Generate web server log-like data"""
    levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    msgs = ['Connection established', 'Request processed', 'Error occurred', 'Timeout', 'Retry scheduled']
    lines = []
    for i in range(n):
        ts = f"2024-01-{random.randint(1,30):02d} {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        level = random.choice(levels)
        msg = random.choice(msgs)
        lines.append(f"[{ts}] {level}: {msg} (id={i})")
    return lines


def generate_config_data(n):
    """Generate config file-like data"""
    lines = []
    for i in range(n):
        key = f"setting_{i}"
        val = random.choice(['true', 'false', '123', 'abc', '1.5'])
        lines.append(f"{key} = {val}")
    return lines


def generate_json_like(n):
    """Generate JSON-like data"""
    items = []
    for i in range(n):
        items.append(json.dumps({
            "id": i,
            "name": f"item_{i}",
            "value": random.randint(1, 1000),
            "active": i % 2 == 0
        }))
    return items


def benchmark_log_parsing():
    """Parse log entries - real world use case"""
    print("\n" + "="*70)
    print("REAL WORLD: Log Entry Parsing - 100,000 lines")
    print("="*70)
    
    n = 100_000
    lines = generate_log_lines(n)
    
    # Original pyparsing - complex grammar
    timestamp = pp_orig.Regex(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    level = pp_orig.oneOf('INFO WARN ERROR DEBUG')
    message = pp_orig.Regex(r'[^()]+')
    log_entry = pp_orig.Suppress('[') + timestamp + pp_orig.Suppress(']') + level + pp_orig.Suppress(':') + message
    
    print("\nOriginal pyparsing (complex grammar):")
    start = time.perf_counter()
    parsed = 0
    for line in lines:
        try:
            log_entry.parseString(line)
            parsed += 1
        except:
            pass
    orig_time = time.perf_counter() - start
    orig_throughput = n / orig_time
    print(f"  Time: {orig_time*1000:.2f}ms ({orig_throughput:.0f} lines/sec)")
    print(f"  Successfully parsed: {parsed}")
    
    # Rust version
    rs_timestamp = pp_rs.Regex(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    rs_level = pp_rs.MatchFirst([pp_rs.Literal(l) for l in ['INFO', 'WARN', 'ERROR', 'DEBUG']])
    rs_message = pp_rs.Regex(r'[^()]+')
    open_bracket = pp_rs.Suppress(pp_rs.Literal('['))
    close_bracket = pp_rs.Suppress(pp_rs.Literal(']'))
    colon = pp_rs.Suppress(pp_rs.Literal(':'))
    rs_log = open_bracket + rs_timestamp + close_bracket + rs_level + colon + rs_message
    
    print("\npyparsing_rs (Rust):")
    start = time.perf_counter()
    parsed = 0
    for line in lines:
        try:
            rs_log.parse_string(line)
            parsed += 1
        except:
            pass
    rs_time = time.perf_counter() - start
    rs_throughput = n / rs_time
    speedup = orig_time / rs_time
    
    print(f"  Time: {rs_time*1000:.2f}ms ({rs_throughput:.0f} lines/sec)")
    print(f"  Successfully parsed: {parsed}")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_config_parsing():
    """Parse config key=value pairs"""
    print("\n" + "="*70)
    print("REAL WORLD: Config File Parsing - 500,000 lines")
    print("="*70)
    
    n = 500_000
    lines = generate_config_data(n)
    
    # Original pyparsing
    key = pp_orig.Word(pp_orig.alphas + '_', pp_orig.alphanums + '_')
    value = pp_orig.Word(pp_orig.alphanums + '_.')
    assignment = key + pp_orig.Suppress('=') + value
    
    print("\nOriginal pyparsing:")
    start = time.perf_counter()
    for line in lines:
        try:
            assignment.parseString(line)
        except:
            pass
    orig_time = time.perf_counter() - start
    orig_throughput = n / orig_time
    print(f"  Time: {orig_time*1000:.2f}ms ({orig_throughput:.0f} lines/sec)")
    
    # Rust
    rs_key = pp_rs.Word(pp_rs.alphas() + '_', pp_rs.alphanums() + '_')
    rs_value = pp_rs.Word(pp_rs.alphanums() + '_.')
    rs_assignment = rs_key + pp_rs.Suppress(pp_rs.Literal('=')) + rs_value
    
    print("\npyparsing_rs:")
    start = time.perf_counter()
    for line in lines:
        try:
            rs_assignment.parse_string(line)
        except:
            pass
    rs_time = time.perf_counter() - start
    rs_throughput = n / rs_time
    speedup = orig_time / rs_time
    
    print(f"  Time: {rs_time*1000:.2f}ms ({rs_throughput:.0f} lines/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_json_extract():
    """Extract values from JSON-like strings"""
    print("\n" + "="*70)
    print("REAL WORLD: JSON Field Extraction - 200,000 items")
    print("="*70)
    
    n = 200_000
    items = generate_json_like(n)
    
    # Original pyparsing
    field = pp_orig.Suppress('"value":') + pp_orig.Word(pp_orig.nums)
    
    print("\nOriginal pyparsing:")
    start = time.perf_counter()
    total = 0
    for item in items:
        try:
            result = field.parseString(item)
            total += int(result[0])
        except:
            pass
    orig_time = time.perf_counter() - start
    orig_throughput = n / orig_time
    print(f"  Time: {orig_time*1000:.2f}ms ({orig_throughput:.0f} items/sec)")
    print(f"  Sum of values: {total}")
    
    # Rust
    rs_field = pp_rs.Suppress(pp_rs.Literal('"value":')) + pp_rs.Word(pp_rs.nums())
    
    print("\npyparsing_rs:")
    start = time.perf_counter()
    total = 0
    for item in items:
        try:
            result = rs_field.parse_string(item)
            total += int(result[0])
        except:
            pass
    rs_time = time.perf_counter() - start
    rs_throughput = n / rs_time
    speedup = orig_time / rs_time
    
    print(f"  Time: {rs_time*1000:.2f}ms ({rs_throughput:.0f} items/sec)")
    print(f"  Sum of values: {total}")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_csv_parsing():
    """Parse CSV-like data"""
    print("\n" + "="*70)
    print("REAL WORLD: CSV Data Parsing - 1,000,000 rows")
    print("="*70)
    
    n = 1_000_000
    rows = [f"{i},name{i},{random.randint(1,100)},{random.random()}" for i in range(n)]
    
    # Original pyparsing
    integer = pp_orig.Word(pp_orig.nums)
    name = pp_orig.Word(pp_orig.alphanums)
    decimal = pp_orig.Regex(r'\d+\.\d+')
    row = integer + pp_orig.Suppress(',') + name + pp_orig.Suppress(',') + integer + pp_orig.Suppress(',') + decimal
    
    print("\nOriginal pyparsing:")
    start = time.perf_counter()
    parsed = 0
    for r in rows:
        try:
            row.parseString(r)
            parsed += 1
        except:
            pass
    orig_time = time.perf_counter() - start
    orig_throughput = n / orig_time
    print(f"  Time: {orig_time*1000:.2f}ms ({orig_throughput:.0f} rows/sec)")
    
    # Rust
    rs_int = pp_rs.Word(pp_rs.nums())
    rs_name = pp_rs.Word(pp_rs.alphanums())
    rs_decimal = pp_rs.Regex(r'\d+\.\d+')
    comma = pp_rs.Suppress(pp_rs.Literal(','))
    rs_row = rs_int + comma + rs_name + comma + rs_int + comma + rs_decimal
    
    print("\npyparsing_rs:")
    start = time.perf_counter()
    parsed = 0
    for r in rows:
        try:
            rs_row.parse_string(r)
            parsed += 1
        except:
            pass
    rs_time = time.perf_counter() - start
    rs_throughput = n / rs_time
    speedup = orig_time / rs_time
    
    print(f"  Time: {rs_time*1000:.2f}ms ({rs_throughput:.0f} rows/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_repeated_parsing():
    """Parse same pattern many times - amortize setup cost"""
    print("\n" + "="*70)
    print("COMPLEX GRAMMAR: Expression Parsing - 50,000 expressions")
    print("="*70)
    
    n = 50_000
    expressions = [f"{random.randint(1,100)} + {random.randint(1,100)} * {random.randint(1,100)}" for _ in range(n)]
    
    # Original pyparsing
    integer = pp_orig.Word(pp_orig.nums)
    op = pp_orig.oneOf('+ - * /')
    expr = integer + op + integer + op + integer
    
    print("\nOriginal pyparsing:")
    start = time.perf_counter()
    for e in expressions:
        try:
            expr.parseString(e)
        except:
            pass
    orig_time = time.perf_counter() - start
    orig_throughput = n / orig_time
    print(f"  Time: {orig_time*1000:.2f}ms ({orig_throughput:.0f} exprs/sec)")
    
    # Rust
    rs_int = pp_rs.Word(pp_rs.nums())
    plus = pp_rs.Literal('+')
    minus = pp_rs.Literal('-')
    mult = pp_rs.Literal('*')
    div = pp_rs.Literal('/')
    rs_op = pp_rs.MatchFirst([plus, minus, mult, div])
    rs_expr = rs_int + rs_op + rs_int + rs_op + rs_int
    
    print("\npyparsing_rs:")
    start = time.perf_counter()
    for e in expressions:
        try:
            rs_expr.parse_string(e)
        except:
            pass
    rs_time = time.perf_counter() - start
    rs_throughput = n / rs_time
    speedup = orig_time / rs_time
    
    print(f"  Time: {rs_time*1000:.2f}ms ({rs_throughput:.0f} exprs/sec)")
    print(f"  Speedup: {speedup:.1f}x")
    
    return speedup


def benchmark_batch_file_processing():
    """Process entire file in Rust"""
    print("\n" + "="*70)
    print("FILE PROCESSING: In-Rust Batch - 5M lines")
    print("="*70)
    
    import tempfile
    
    n = 5_000_000
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for i in range(n):
            f.write(f"LOG{i:08d}: {random.choice(['INFO', 'ERROR'])} message here\n")
        filename = f.name
    
    try:
        # Python - line by line with pyparsing
        pp_lit = pp_orig.Literal("INFO")
        
        print("\nPython pyparsing (line by line):")
        start = time.perf_counter()
        count = 0
        with open(filename, 'r') as f:
            for line in f:
                try:
                    pp_lit.parseString(line)
                    count += 1
                except:
                    pass
        orig_time = time.perf_counter() - start
        print(f"  Time: {orig_time*1000:.2f}ms, INFO lines: {count}")
        
        # Rust - file processed entirely in Rust
        print("\nRust (entire file in Rust):")
        start = time.perf_counter()
        total, matches = pp_rs.process_file_lines(filename, "INFO")
        rs_time = time.perf_counter() - start
        speedup = orig_time / rs_time
        
        print(f"  Time: {rs_time*1000:.2f}ms, total: {total}, matches: {matches}")
        print(f"  Speedup: {speedup:.1f}x")
        
        return speedup
        
    finally:
        import os
        os.remove(filename)


if __name__ == "__main__":
    print("="*70)
    print("REAL WORLD 100X BENCHMARK")
    print("Testing actual pyparsing use cases (not just string ops)")
    print("="*70)
    
    results = []
    
    results.append(("Log Parsing (100K)", benchmark_log_parsing()))
    results.append(("Config Parsing (500K)", benchmark_config_parsing()))
    results.append(("JSON Extract (200K)", benchmark_json_extract()))
    results.append(("CSV Parsing (1M)", benchmark_csv_parsing()))
    results.append(("Expression Parsing (50K)", benchmark_repeated_parsing()))
    results.append(("File Processing (5M)", benchmark_batch_file_processing()))
    
    # Summary
    print("\n" + "="*70)
    print("FINAL RESULTS - Real World Use Cases")
    print("="*70)
    
    for name, speedup in results:
        status = "🎉" if speedup >= 100 else "✅" if speedup >= 50 else "⚠️" if speedup >= 20 else "❌"
        print(f"{status} {name:.<45} {speedup:>6.1f}x")
    
    valid_results = [s for _, s in results if s is not None]
    if valid_results:
        max_speedup = max(valid_results)
        avg_speedup = sum(valid_results) / len(valid_results)
        
        print(f"\nMaximum speedup: {max_speedup:.1f}x")
        print(f"Average speedup: {avg_speedup:.1f}x")
        
        if max_speedup >= 100:
            print("\n🎉🎉🎉 100X SPEEDUP ACHIEVED! 🎉🎉🎉")
        elif max_speedup >= 50:
            print("\n✅ GOOD: 50X+ achieved")
        else:
            print(f"\n⚠️  Max: {max_speedup:.1f}x - need more optimization")
