#!/usr/bin/env python3
"""Baseline benchmarks for original pyparsing library."""
import time
import statistics
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "test_grammars"))

RESULTS_FILE = Path("/home/aibrush/pyparsing-rs/baseline_results.json")
ITERATIONS = 10

def benchmark(func, iterations=ITERATIONS):
    """Run function multiple times and return stats."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        func()
        end = time.perf_counter_ns()
        times.append(end - start)
    return {
        "mean_ns": statistics.mean(times),
        "median_ns": statistics.median(times),
        "min_ns": min(times),
        "max_ns": max(times),
        "stdev_ns": statistics.stdev(times) if len(times) > 1 else 0,
        "iterations": iterations
    }

def run_benchmarks():
    results = {}
    
    # Arithmetic expression benchmark
    print("Benchmarking arithmetic expressions...")
    from arithmetic import run_benchmark as arith_bench, TEST_EXPRESSIONS
    results["arithmetic"] = benchmark(arith_bench)
    results["arithmetic"]["num_parses"] = len(TEST_EXPRESSIONS)
    
    # JSON-like grammar benchmark
    print("Benchmarking JSON-like grammar...")
    from json_grammar import run_benchmark as json_bench, TEST_JSON
    results["json_grammar"] = benchmark(json_bench)
    results["json_grammar"]["num_parses"] = len(TEST_JSON)
    
    # Config file benchmark
    print("Benchmarking config file grammar...")
    from config_file import run_benchmark as config_bench, TEST_CONFIGS
    results["config_file"] = benchmark(config_bench)
    results["config_file"]["num_parses"] = len(TEST_CONFIGS)
    
    # Simple literal matching benchmark
    print("Benchmarking simple literals...")
    import pyparsing as pp
    literal = pp.Literal("hello")
    test_strings = ["hello world"] * 10000
    
    def literal_bench():
        for s in test_strings:
            try:
                literal.parse_string(s)
            except pp.ParseException:
                pass
    
    results["simple_literal"] = benchmark(literal_bench)
    results["simple_literal"]["num_parses"] = len(test_strings)
    
    # Word matching benchmark
    print("Benchmarking Word matching...")
    word = pp.Word(pp.alphas)
    test_words = ["helloworld", "foo", "bar", "testing", "pyparsing"] * 2000
    
    def word_bench():
        for w in test_words:
            try:
                word.parse_string(w)
            except pp.ParseException:
                pass
    
    results["word_match"] = benchmark(word_bench)
    results["word_match"]["num_parses"] = len(test_words)
    
    # Regex matching benchmark
    print("Benchmarking Regex matching...")
    regex = pp.Regex(r"\d{4}-\d{2}-\d{2}")
    test_dates = ["2024-01-15", "2023-12-31", "2025-06-30"] * 3000
    
    def regex_bench():
        for d in test_dates:
            try:
                regex.parse_string(d)
            except pp.ParseException:
                pass
    
    results["regex_match"] = benchmark(regex_bench)
    results["regex_match"]["num_parses"] = len(test_dates)
    
    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nBaseline results saved to {RESULTS_FILE}")
    print("\nSummary (mean times per batch):")
    for name, stats in results.items():
        per_parse = stats['mean_ns'] / stats['num_parses'] / 1000
        print(f"  {name}: {stats['mean_ns']/1e6:.2f} ms total, {per_parse:.2f} µs/parse")
    
    return results

if __name__ == "__main__":
    run_benchmarks()
