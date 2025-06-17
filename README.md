# BCKL – Backlog Dictation CLI

[![CI Status](https://github.com/theplaylabs/Backlog_tool_1/actions/workflows/ci.yml/badge.svg)](https://github.com/theplaylabs/Backlog_tool_1/actions/workflows/ci.yml)

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
| `BACKLOG_MODEL`  | Chat completion model | `gpt-4o-mini` |
| `BACKLOG_LOG_DIR`| Folder for logs | `%USERPROFILE%\.bckl` |
| `BACKLOG_LOG_LEVEL` | Root log level | `INFO` |

Place them in `.env` (auto-loaded) or in your shell profile.

---

## Demo

See the [demo instructions](docs/demo.md) for recording a demonstration GIF.

---

## Usage
```powershell
# Typical: microphone dictation piped in via wintools/mac tools
Get-Content dictation.txt | bckl

# Safe dry-run – just show JSON
bckl --dry-run < idea.txt
```

Flags:
* `--dry-run` – validate via OpenAI but _do not_ touch `backlog.csv`.
* `--version` – display current app version.

### Output Format

When a dictation is processed, the output will include:
1. A separator line
2. The title and difficulty rating
3. Another separator line
4. The full description text

### Customizing the Prompt

The OpenAI prompt used to process dictations is stored in `prompt.txt` in the project root. You can edit this file to customize how dictations are interpreted without modifying code.

### CSV File

The tool automatically creates `backlog.csv` in the current directory if it doesn't exist. Each entry is stored in the following format:

```
title, difficulty, description, timestamp
```

Entries are prepended to the file, so the most recent items appear at the top.

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

## Architecture

See the [architecture diagram](docs/architecture.md) for component overview and data flow.

---

## Release Process

To create a new release:

```powershell
# Build the package
./scripts/build.ps1

# Test installation in clean environment
./scripts/test_install.ps1

# Create release with version
./scripts/release.ps1 -Version 0.1.0 -TestPyPI
```

See `tasks/tasks-prd-backlog-cli.md` for project history and completed milestones.
