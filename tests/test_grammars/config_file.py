#!/usr/bin/env python3
"""INI-like config file grammar for benchmarking."""
import pyparsing as pp

# Config grammar
comment = pp.Regex(r"#.*").suppress()
key = pp.Word(pp.alphanums + "_")
value = pp.Regex(r"[^\n#]+").set_parse_action(lambda t: t[0].strip())
assignment = pp.Group(key + pp.Suppress("=") + value)
section_header = pp.Suppress("[") + pp.Word(pp.alphanums + "_") + pp.Suppress("]")
section = pp.Group(section_header + pp.Group(pp.ZeroOrMore(assignment | comment)))
config = pp.ZeroOrMore(section | comment)

# Test data
TEST_CONFIG = """
[database]
host = localhost
port = 5432
name = mydb
user = admin

[server]
host = 0.0.0.0
port = 8080
debug = true
workers = 4

[logging]
level = INFO
format = json
file = /var/log/app.log
""".strip()

# Repeat config for benchmarking
TEST_CONFIGS = [TEST_CONFIG] * 100

def run_benchmark():
    results = []
    for c in TEST_CONFIGS:
        try:
            results.append(config.parse_string(c))
        except pp.ParseException:
            pass
    return results

if __name__ == "__main__":
    import time
    start = time.perf_counter()
    run_benchmark()
    end = time.perf_counter()
    print(f"Parsed {len(TEST_CONFIGS)} configs in {end-start:.4f}s")
