import subprocess
import pytest

pytestmark = pytest.mark.integration
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(input_text: str, cwd: Path):
    return subprocess.run(
        [sys.executable, "-m", "backlog_cli.cli"],
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_cli_full_run(tmp_path):
    # Run in temp directory, verify CSV created and contains row
    result = _run_cli("Do thing\n", tmp_path)
    assert result.returncode == 0, result.stderr
    csv_path = tmp_path / "backlog.csv"
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8").strip()
    assert content  # non-empty
    assert content.count("\n") == 0  # exactly one row


def test_cli_nested_dir(tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    result = _run_cli("Another item\n", nested)
    assert result.returncode == 0
    csv_path = nested / "backlog.csv"
    assert csv_path.exists()
