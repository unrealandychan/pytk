import pytest
from pytk.filters.cargo import CargoFilter

f = CargoFilter()


def test_matches_cargo():
    assert f.matches(["cargo", "build"])

def test_matches_rustc():
    assert f.matches(["rustc", "main.rs"])

def test_matches_rustfmt():
    assert f.matches(["rustfmt", "src/lib.rs"])

def test_no_match():
    assert not f.matches(["python", "main.py"])
    assert not f.matches([])


def test_cargo_build_strips_compiling():
    lines = [f"   Compiling foo v1.0.0 (path)" for _ in range(5)]
    lines.append("   Finished dev [unoptimized] target(s) in 2.5s")
    raw = "\n".join(lines)
    out = f._filter_build(raw, {})
    assert "Compiling 5 crates" in out
    assert "Compiling foo v1.0.0" not in out
    assert "Finished" not in out


def test_cargo_build_keeps_errors():
    raw = """   Compiling myapp v0.1.0
error[E0308]: mismatched types
 --> src/main.rs:10:5
  |
10|     42
  |     ^^ expected `()`, found integer
   Finished dev target(s) in 1.0s"""
    out = f._filter_build(raw, {})
    assert "error[E0308]" in out
    assert "mismatched types" in out


def test_cargo_test_strips_passing():
    lines = [f"test foo::bar_{i} ... ok" for i in range(10)]
    lines.append("test foo::baz ... FAILED")
    lines.append("")
    lines.append("test result: FAILED. 0 passed; 1 failed; 0 ignored")
    raw = "\n".join(lines)
    out = f._filter_test(raw)
    assert "FAILED" in out
    assert "test result:" in out
    assert "... ok" not in out


def test_cargo_clippy_strips_checking():
    raw = """   Checking mycrate v0.1.0 (path)
warning: unused variable `x`
 --> src/main.rs:5:9
  |
5|     let x = 1;
  |         ^ help: if this is intentional...
  = help: for further information visit https://example.com
warning: 1 warning emitted"""
    out = f._filter_clippy(raw)
    assert "Checking mycrate" not in out
    assert "= help:" not in out
    assert "unused variable" in out
    assert "warning: 1 warning emitted" in out


def test_cargo_add_compressed():
    raw = """    Updating crates.io index
      Adding serde v1.0.195 to dependencies
    Updating Cargo.lock"""
    out = f._filter_add_update(raw)
    assert "serde" in out
