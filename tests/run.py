"""Dependency-free test runner: every tests/test_*.py, every test_* function."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))


def main() -> int:
    failed = 0
    total = 0
    for path in sorted(ROOT.glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in sorted(n for n in dir(module) if n.startswith("test_")):
            fn = getattr(module, name)
            if not callable(fn):
                continue
            total += 1
            try:
                fn()
            except Exception:
                failed += 1
                print(f"FAIL {path.stem}.{name}")
                traceback.print_exc()
            else:
                print(f"PASS {path.stem}.{name}")
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
