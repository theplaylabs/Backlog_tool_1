from pathlib import Path

import os
import io
import csv
import builtins

import backlog_cli.csv_store as cs


def test_quote_and_newline(tmp_path):
    csv_path = tmp_path / "backlog.csv"
    row = [
        "2025-01-01T00:00:00Z",
        "Title with, comma",
        "5",
        "Multiline\nDescription with, commas and \"quotes\"",
    ]
    cs.prepend_row(csv_path, row)
    # Read back with csv module to ensure correct parsing
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        read_row = next(reader)
    assert read_row == row


def test_file_locked_handled(tmp_path, capsys, monkeypatch):
    csv_path = tmp_path / "backlog.csv"
    csv_path.write_text("dummy\n", encoding="utf-8")

    def _raise(*_a, **_kw):
        raise PermissionError("locked")

    monkeypatch.setattr(os, "replace", _raise)
    cs.prepend_row(csv_path, ["t", "x", "1", "d"])
    captured = capsys.readouterr()
    assert "WARNING: could not write CSV" in captured.out
    # Original file remains unchanged
    assert csv_path.read_text(encoding="utf-8") == "dummy\n"


def test_large_file(tmp_path):
    csv_path = tmp_path / "backlog.csv"
    # create 6000 rows
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        for i in range(6000):
            f.write(f"row{i}\n")
    cs.prepend_row(csv_path, ["new", "t", "1", "d"])
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("new,")
    assert len(lines) == 6001
