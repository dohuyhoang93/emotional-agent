
import theus

def test_version_bump():
    print(f"Theus Version: {theus.__version__}")
    # We verify it matches the cargo.toml/pyproject.toml expectation (v3.0.x +)
    assert theus.__version__.startswith("3.1."), f"Version mismatch: {theus.__version__}"
    assert theus.__version__ >= "3.1.2", "Old version detected"
