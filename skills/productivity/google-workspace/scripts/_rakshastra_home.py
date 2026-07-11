"""Resolve RAKSHASTRA_HOME for standalone skill scripts.

Skill scripts may run outside the Rakshastra process (e.g. system Python,
nix env, CI) where ``rakshastra_constants`` is not importable.  This module
provides the same ``get_rakshastra_home()`` and ``display_rakshastra_home()``
contracts as ``rakshastra_constants`` without requiring it on ``sys.path``.

When ``rakshastra_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``rakshastra_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``RAKSHASTRA_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from rakshastra_constants import display_rakshastra_home as display_rakshastra_home
    from rakshastra_constants import get_rakshastra_home as get_rakshastra_home
except (ModuleNotFoundError, ImportError):

    def get_rakshastra_home() -> Path:
        """Return the Rakshastra home directory (default: ~/.rakshastra).

        Mirrors ``rakshastra_constants.get_rakshastra_home()``."""
        val = os.environ.get("RAKSHASTRA_HOME", "").strip()
        return Path(val) if val else Path.home() / ".rakshastra"

    def display_rakshastra_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``rakshastra_constants.display_rakshastra_home()``."""
        home = get_rakshastra_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
