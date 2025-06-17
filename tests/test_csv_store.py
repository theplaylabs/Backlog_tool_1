from pathlib import Path

import backlog_cli.csv_store as cs


def test_prepend_new_file(tmp_path):
    csv_path = tmp_path / "backlog.csv"
    cs.prepend_row(csv_path, ["2025-01-01T00:00:00Z", "Test", "1", "Desc"])
    assert csv_path.read_text(encoding="utf-8").startswith("2025-01-01T00:00:00Z")


def test_prepend_existing(tmp_path):
    csv_path = tmp_path / "backlog.csv"
    csv_path.write_text("old\n", encoding="utf-8")
    cs.prepend_row(csv_path, ["n", "t", "d", "x"])
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("n,")
