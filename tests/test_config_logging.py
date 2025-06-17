import os
import pytest

pytestmark = pytest.mark.new
from pathlib import Path

import backlog_cli.config as cfg


def test_load_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    c = cfg.load_config()
    assert c.model == "gpt-4o-mini"
    assert c.log_dir == tmp_path / ".bckl"


def test_logging_creates_file(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKLOG_LOG_DIR", str(tmp_path))
    c = cfg.load_config()
    cfg.setup_logging(c)
    log_file = c.log_dir / "bckl.log"
    assert log_file.exists()
    # write a log entry
    logger = cfg.get_logger("test")
    logger.info("hello")
    assert log_file.read_text(encoding="utf-8")
