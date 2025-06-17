"""CSV storage utilities for backlog entries.

The CSV has **no header** and each row is:
title, difficulty (1-5), description, ISO-8601 timestamp

This module provides atomic file operations to ensure data integrity
even when the file is being accessed by multiple processes.
"""
from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Sequence

__all__ = ["prepend_row"]


def _safe_temp_path(target: Path) -> Path:
    """Return a temp file path in the same directory as *target*.
    
    Creates a temporary file in the same directory as the target file.
    This ensures atomic file operations work correctly across filesystems.
    
    Args:
        target: The target file path
        
    Returns:
        Path: Path to a temporary file
    """
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".bckl_tmp_", suffix=".csv")
    os.close(fd)  # we will reopen later with csv API
    return Path(tmp)


def prepend_row(path: Path, row: Sequence[str]) -> None:  # noqa: D401
    """Prepend *row* to *path* atomically.

    * Creates the file if it doesn't exist.
    * Writes using UTF-8 and `csv.QUOTE_MINIMAL` quoting.
    * Uses a temp file + `os.replace` for atomicity on Windows.
    
    Args:
        path: Path to the CSV file
        row: Sequence of strings to write as a CSV row
        
    Note:
        If a permission error occurs (e.g., file locked by another process),
        a warning is printed but no exception is raised.
    """
    temp_path = None
    try:
        temp_path = _safe_temp_path(path)
        
        # Write new row first to temporary file
        with temp_path.open("w", encoding="utf-8", newline="") as tmp_f:
            writer = csv.writer(tmp_f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(row)
            
            # If the target file exists, append its contents to the temp file
            if path.exists():
                # Stream-copy existing data
                with path.open("r", encoding="utf-8", newline="") as orig_f:
                    for line in orig_f:
                        tmp_f.write(line)
        
        # Perform atomic replace operation
        os.replace(temp_path, path)
        
    except PermissionError as exc:
        # Likely file locked – warn but do not raise to keep CLI responsive
        print(f"WARNING: could not write CSV due to permission error: {exc}")
    except Exception as exc:
        # Log other exceptions but don't crash
        print(f"ERROR: failed to write to CSV: {exc}")
    finally:
        # Clean up temp file if something went wrong
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

