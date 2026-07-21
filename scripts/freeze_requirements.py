"""Write a pip freeze snapshot when uv locking is unavailable.

This helper is intentionally not part of `just check`. It gives maintainers a
repeatable fallback artifact when `uv lock` is blocked by local TLS or network
configuration.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    output_path = Path("requirements-freeze.txt")
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    output_path.write_text(completed.stdout, encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
