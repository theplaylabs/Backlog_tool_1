# Advanced Usage

> **Audience**: power-users & CI maintainers

---

## Configuration Matrix

BCKL is zero-config by default; tweak behaviour via **environment variables**.
All vars are read on every run – no restart needed.

| Variable | Effect | Typical Use |
|----------|--------|-------------|
| `BACKLOG_MODEL` | override chat model | switch to `gpt-4o` when approved |
| `BACKLOG_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | verbose troubleshooting |
| `BACKLOG_LOG_DIR` | absolute / tilde-expanded path for rotating logs | direct logs to project folder in CI |

### Example `.env`
```env
OPENAI_API_KEY=sk-...
BACKLOG_MODEL=gpt-3.5-turbo-0125
BACKLOG_LOG_LEVEL=DEBUG
```

A local `.env` file is automatically loaded if present (via `python-dotenv`).

---

## Verbose Mode vs Dry-Run

| Flag | Description | Exit code |
|------|-------------|-----------|
| `--verbose` | prints the **description** field after save | 0 |
| `--dry-run` | talks to OpenAI but **does not** touch `backlog.csv` | 0 |

Verbose + dry-run together are allowed: you’ll see the parsed JSON **and** the
full description.

---

## Continuous Integration

The repository ships with a Windows workflow that executes the *fast* test
suite (`pytest -m "not integration"`). To run the full suite add a matrix job
or trigger on a schedule:

```yaml
jobs:
  nightly:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: "3.11" }
      - run: pip install -e .[dev]
      - run: pytest -q  # full suite including integration
```

Add a badge to your README:
```markdown
![CI](https://github.com/your-org/Backlog_tool_1/actions/workflows/ci.yml/badge.svg)
```

---

## Programmatic Import

The CLI functions are accessible from Python:
```python
from backlog_cli import config, cli, csv_store, openai_client

cfg = config.load_config()
print("Current model:", cfg.model)
```

---

## FAQ

**Q: How do I change where `backlog.csv` is written?**  
A: Simply `cd` to the desired folder before invoking `bckl`; the tool always
uses the *current working directory*.

**Q: Can I use Azure OpenAI?**  
Not yet. A provider abstraction is on the roadmap after v0.1.0.
