# Lessons Learned from emailval Project

## CI/CD Setup

### GitHub Actions Workflow Structure
- Use `dtolnay/rust-toolchain@stable` for Rust setup (not `rust-action`)
- Use `actions/setup-python@v5` for Python
- Use `Swatinem/rust-cache@v2` for Cargo caching
- Use `actions/cache@v4` for pip dependencies

### Caching Strategy (6 hours)
```yaml
- name: Cache cargo (6 hours)
  uses: Swatinem/rust-cache@v2
  with:
    shared-key: "rust-cache"
    cache-directories: |
      ~/.cargo/registry
      ~/.cargo/git
      target

- name: Cache pip dependencies (6 hours)
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/pyproject.toml') }}
    restore-keys: |
      ${{ runner.os }}-pip-${{ matrix.python-version }}-
      ${{ runner.os }}-pip-
```

### Release on Merge to Main
- Trigger release workflow on `push: branches: [main]`
- Check version from pyproject.toml
- Skip if tag already exists
- Create tag after successful PyPI publish

### PyPI Publishing
- Use `maturin publish --non-interactive` with `MATURIN_PYPI_TOKEN` env var
- Do NOT use `--token` flag (deprecated)
- Build wheels for all platforms (Linux, macOS, Windows)
- Build for Python 3.9-3.13

## Project Structure

### Cargo.toml
```toml
[profile.release]
lto = true
codegen-units = 1
panic = "abort"
strip = true
opt-level = 3
```

### Workspace Structure
```
project/
├── Cargo.toml              # Workspace root
├── crates/
│   └── core/               # Rust core library
├── wrappers/
│   └── python/             # Python bindings
│       ├── Cargo.toml
│       ├── pyproject.toml
│       └── src/
├── .github/workflows/
│   ├── ci.yml              # Test on branches
│   └── release.yml         # Release on merge to main
└── docs/
```

## Common Issues & Solutions

### maturin develop fails
Need virtualenv or use `maturin build` + `pip install`

### GitHub Actions: wheel paths
Wheels go to `target/wheels/` at repo root, not `wrappers/python/target/wheels/`

### Clippy warnings
- Use `(range).contains(&value)` instead of manual range checks
- Use `iter().enumerate()` instead of index loops
- Collapse nested if statements

### PyPI name conflicts
Check availability before starting. Have backup names ready.

## Performance Optimizations

### Rust side
- Use lookup tables for O(1) character checks
- Use SWAR (SIMD Within A Register) for byte scanning
- Zero-copy validation where possible
- `#[inline]` on hot paths

### Python side
- FFI overhead is ~108ns minimum
- Batch operations to amortize FFI cost
- Use `__slots__` for Python classes

## Testing

### Structure
- `tests/test_api_compat.py` - API compatibility tests
- `tests/test_performance.py` - Benchmark comparisons
- `test_grammars/` - Sample grammars for testing

### Baseline Benchmarking
- Save baseline results before starting
- Compare against original library
- Target: 50-200x speedup

## Documentation

### Files to create
- `README.md` - Project overview, quick start
- `docs/README.md` - Documentation index
- `docs/installation.md` - Installation guide
- `docs/quickstart.md` - Getting started
- `docs/api.md` - API reference
- `docs/architecture.md` - Technical details
- `docs/contributing.md` - Contribution guide
- `docs/changelog.md` - Version history

## Version Management

- Update version in all Cargo.toml files
- Update version in pyproject.toml
- Update CHANGELOG.md
- Create git tag after successful release
