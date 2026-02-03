#!/usr/bin/env python3
"""Simple arithmetic expression grammar for benchmarking."""
import pyparsing as pp

# Define grammar
integer = pp.Word(pp.nums)
real = pp.Combine(pp.Word(pp.nums) + "." + pp.Word(pp.nums))
number = real | integer
variable = pp.Word(pp.alphas, pp.alphanums + "_")

operand = number | variable
add_op = pp.one_of("+ -")
mul_op = pp.one_of("* /")

expr = pp.infix_notation(
    operand,
    [
        (mul_op, 2, pp.opAssoc.LEFT),
        (add_op, 2, pp.opAssoc.LEFT),
    ]
)

# Test data
TEST_EXPRESSIONS = [
    "1 + 2",
    "3 * 4 + 5",
    "x + y * z",
    "a * b + c * d",
    "(1 + 2) * 3",
    "10 / 2 - 3 + 4 * 5",
    "foo + bar * baz - qux / quux",
    "1.5 + 2.7 * 3.14159",
] * 50  # 400 expressions

def run_benchmark():
    """Parse all test expressions."""
    results = []
    for e in TEST_EXPRESSIONS:
        try:
            results.append(expr.parse_string(e))
        except pp.ParseException:
            pass
    return results

if __name__ == "__main__":
    import time
    start = time.perf_counter()
    run_benchmark()
    end = time.perf_counter()
    print(f"Parsed {len(TEST_EXPRESSIONS)} expressions in {end-start:.4f}s")
