"""CSV storage utilities for backlog entries.

The CSV has **no header** and each row is:
ISO-8601 timestamp, title, difficulty (1-5), description
"""
from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Sequence

__all__ = ["prepend_row"]


def _safe_temp_path(target: Path) -> Path:
    """Return a temp file path in the same directory as *target*."""
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".bckl_tmp_", suffix=".csv")
    os.close(fd)  # we will reopen later with csv API
    return Path(tmp)


def prepend_row(path: Path, row: Sequence[str]) -> None:  # noqa: D401
    """Prepend *row* to *path* atomically.

    * Creates the file if it doesn't exist.
    * Writes using UTF-8 and `csv.QUOTE_MINIMAL` quoting.
    * Uses a temp file + `os.replace` for atomicity on Windows.
    """
    try:
        temp_path = _safe_temp_path(path)
        # Write new row first
        with temp_path.open("w", encoding="utf-8", newline="") as tmp_f:
            writer = csv.writer(tmp_f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(row)
            if path.exists():
                # Stream-copy existing data
                with path.open("r", encoding="utf-8", newline="") as orig_f:
                    for line in orig_f:
                        tmp_f.write(line)
        # Atomic replace
        os.replace(temp_path, path)
    except PermissionError as exc:
        # Likely file locked – warn but do not raise to keep CLI responsive
        print(f"WARNING: could not write CSV due to permission error: {exc}")
    finally:
        # Clean up temp file if something went wrong
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

