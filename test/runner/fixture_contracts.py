"""Resolve each framework version's authoritative validation fixture."""
from pathlib import Path


def expected_file(scenario, declared="excepted.yml"):
    root = Path(scenario).resolve()
    path = (root / declared).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"declared validation fixture is missing or outside its scenario: {declared}")
    return path.relative_to(root).as_posix()
