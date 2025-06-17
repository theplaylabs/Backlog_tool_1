# BCKL – Backlog Dictation CLI

_BCKL turns a voice-dictated idea into a structured backlog entry and
appends it (atomically) to `backlog.csv` in the current folder._

---

## Installation

### Quick install (isolated)
```powershell
pipx install git+https://github.com/your-org/bckl.git
# `bckl` will now be on PATH
```

### Development workflow
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]   # editable + test deps
```

---

## Environment / Configuration
| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | API key for OpenAI | _required_ |
| `BACKLOG_MODEL`  | Chat completion model | `gpt-3.5-turbo` |
| `BACKLOG_LOG_DIR`| Folder for logs | `%USERPROFILE%\.bckl` |
| `BACKLOG_LOG_LEVEL` | Root log level | `INFO` |

Place them in `.env` (auto-loaded) or in your shell profile.

---

## Usage
```powershell
# Typical: microphone dictation piped in via wintools/mac tools
Get-Content dictation.txt | bckl --verbose

# Safe dry-run – just show JSON
bckl --dry-run < idea.txt
```

Flags:
* `--dry-run` – validate via OpenAI but _do not_ touch `backlog.csv`.
* `--verbose` – print the full description field after saving.
* `--version` – display current app version.

Logging goes to `%USERPROFILE%\.bckl\bckl.log` (rotating, 0.5 MB × 3).

---

## Testing
```powershell
# only actively failing / brand-new tests
pytest -m new -q

# fast regression (skip slow integration)
pytest -m "not integration" -q

# full suite
pytest -q
```

### Markers
```
new          – recently added tests you’re fixing now
integration  – slow end-to-end tests
```

---

## Troubleshooting
| Symptom | Resolution |
|---------|------------|
| `openai.AuthenticationError` | Verify `OPENAI_API_KEY` exported / in `.env`. |
| Network timeouts | Re-run (client retries); check firewalls. |
| `PermissionError` writing `backlog.csv` | Ensure file not open in Excel/Sheets. |

---

## Roadmap
See `tasks/tasks-prd-backlog-cli.md` for remaining milestones (logging, CI,
documentation, release pipeline).
