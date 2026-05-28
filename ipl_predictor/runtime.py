from __future__ import annotations

import sys


def require_supported_python() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 13):
        raise RuntimeError(
            f"Unsupported Python {major}.{minor}. Use CPython 3.12.x or 3.11.x."
        )
