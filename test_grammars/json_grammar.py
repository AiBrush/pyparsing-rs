#!/usr/bin/env python3
"""JSON-like grammar for benchmarking (without using built-in JSON)."""
import pyparsing as pp

# Define JSON grammar with pyparsing
LBRACE, RBRACE, LBRACK, RBRACK, COLON, COMMA = map(pp.Suppress, "{}[]:,")

json_string = pp.QuotedString('"', esc_char='\\')
json_number = pp.pyparsing_common.number
json_bool = pp.one_of("true false null").set_parse_action(
    lambda t: {"true": True, "false": False, "null": None}[t[0]]
)

json_value = pp.Forward()
json_array = pp.Group(LBRACK + pp.Optional(pp.DelimitedList(json_value)) + RBRACK)
json_object = pp.Dict(pp.Group(
    LBRACE + pp.Optional(pp.DelimitedList(
        pp.Group(json_string + COLON + json_value)
    )) + RBRACE
))

json_value <<= json_string | json_number | json_bool | json_array | json_object

# Test data
TEST_JSON = [
    '{"name": "John", "age": 30}',
    '{"list": [1, 2, 3, 4, 5]}',
    '{"nested": {"a": 1, "b": {"c": 2}}}',
    '{"mixed": [1, "two", true, null, {"key": "value"}]}',
    '{"empty_obj": {}, "empty_arr": []}',
] * 80  # 400 JSON objects

def run_benchmark():
    results = []
    for j in TEST_JSON:
        try:
            results.append(json_value.parse_string(j))
        except pp.ParseException:
            pass
    return results

if __name__ == "__main__":
    import time
    start = time.perf_counter()
    run_benchmark()
    end = time.perf_counter()
    print(f"Parsed {len(TEST_JSON)} JSON objects in {end-start:.4f}s")
