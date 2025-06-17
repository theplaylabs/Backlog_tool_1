import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cli_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "backlog_cli.cli", "--dry-run"],
        cwd=PROJECT_ROOT,
        input="Dummy feature idea\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "title" in result.stdout
