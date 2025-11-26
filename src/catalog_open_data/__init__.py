"""Package entrypoint wiring."""

from __future__ import annotations

from typing import Any

__all__ = ["main"]


def main(*args: Any, **kwargs: Any) -> Any:
    """Defer importing click/rich until the CLI is actually executed."""

    from .main import main as cli_main

    return cli_main(*args, **kwargs)
