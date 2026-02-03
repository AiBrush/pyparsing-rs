#!/usr/bin/env python3
"""Test arithmetic expression parsing."""
import sys
import time
sys.path.insert(0, '/home/aibrush/pyparsing-rs/test_grammars')

# First benchmark original pyparsing
from arithmetic import run_benchmark as orig_benchmark, TEST_EXPRESSIONS

print("="*60)
print("Benchmarking original pyparsing...")
start = time.perf_counter()
orig_benchmark()
orig_time = time.perf_counter() - start
print(f"Original: {orig_time:.4f}s for {len(TEST_EXPRESSIONS)} expressions")

# Now test our implementation
print("\n" + "="*60)
print("Testing pyparsing_rs...")

import pyparsing_rs as pp

# Build arithmetic grammar
integer = pp.Word(pp.nums())

# Simple test first
print("\nBasic tests:")
result = integer.parse_string("123")
print(f"  integer.parse_string('123') = {result}")

# Test with original expressions
print("\nParsing expressions...")
import pyparsing as orig_pp

orig_integer = orig_pp.Word(orig_pp.nums)
errors = 0
for expr in TEST_EXPRESSIONS[:10]:  # Test first 10
    try:
        orig_result = orig_integer.parse_string(expr.split()[0])
        our_result = integer.parse_string(expr.split()[0])
        if orig_result[0] != our_result[0]:
            print(f"  Mismatch for '{expr}': orig={orig_result}, ours={our_result}")
            errors += 1
    except Exception as e:
        print(f"  Error for '{expr}': {e}")
        errors += 1

if errors == 0:
    print("  All tests passed!")
else:
    print(f"  {errors} errors")
