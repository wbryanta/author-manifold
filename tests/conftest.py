"""Test configuration: make the package and the CLI tools importable.

Prefer `pip install -e .` (src layout); these inserts are a fallback so the
suite also runs from a bare checkout, and they put `tools/` on the path for
the tests that import the CLI modules directly.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

for path in (REPO_ROOT / "src", REPO_ROOT / "tools", REPO_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
