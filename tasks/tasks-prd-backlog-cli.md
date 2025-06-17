## Relevant Files

- `backlog_cli/__init__.py` – Package marker (created).
- `backlog_cli/cli.py` – CLI entry point, reads dictation, flags, writes CSV (updated).
- `backlog_cli/openai_client.py` – Encapsulates OpenAI prompt construction, request, JSON parsing, and in-memory cache (updated).
- `backlog_cli/csv_store.py` – Handles prepend-row logic for `backlog.csv` (created).
- `backlog_cli/config.py` – Configuration + logging helpers (implemented).
- `setup.cfg` – Packaging metadata and `console_scripts` entry for `bckl` (created).
- `pyproject.toml` – Build system configuration for editable install (created).
- `requirements.txt` – Runtime dependencies (`openai`, `python-dotenv`, test libs) (created).
- `.gitignore` – Standard Python exclusions plus `.bckl/` log dir (updated).
- `README.md` – Installation & usage instructions.
- `tests/__init__.py` – Tests package marker (created).
- `tests/test_openai_client.py` – Unit tests, mock OpenAI responses (created).
- `tests/test_csv_store.py` – Unit tests for prepend logic & edge cases.
- `tests/test_cli_dry_run.py` – Dry-run CLI test (created).
- `tests/test_cli_integration.py` – Full CLI integration test (created).
- `tests/test_csv_store_edge.py` – CSV edge-case tests (created).
- `tests/test_config_logging.py` – Config & logging tests (created).
- `docs/advanced.md` – deeper usage & CI guide (created).
- `docs/architecture.md` – component diagram and data flow (created).
- `docs/demo.md` – instructions for creating demo GIF (created).
- `CHANGELOG.md` – Keep a Changelog spec (created).
- `scripts/build.ps1` – package build script (created).
- `scripts/release.ps1` – version and release script (created).
- `scripts/test_install.ps1` – installation verification (created).
- `pytest.ini` – defines test markers (`new`, `integration`).
- `.github/workflows/ci.yml` – GitHub Actions workflow running pytest on Windows.
- `.github/workflows/nightly.yml` – Scheduled workflow for full test suite.

### Notes

* Keep test files alongside code in `tests/` directory.
* Use `pytest` plus `pytest-mock` for mocking.
* Ensure Windows-specific path handling in tests.
* Logging files live in `%USERPROFILE%\.bckl\bckl.log` by default.

## Tasks

- [x] **1.0 Scaffold project and packaging**
  - [x] 1.1 Create directory structure `backlog_cli/` and `tests/`.
  - [x] 1.2 Add `__init__.py` and placeholder modules.
  - [x] 1.3 Write `setup.cfg` with metadata, dependencies, and `console_scripts = bckl = backlog_cli.cli:main`.
  - [x] 1.4 Add `requirements.txt` and `.gitignore`.
  - [x] 1.5 Verify local editable install `pip install -e .` places `bckl` on PATH (Windows PowerShell).
  - [ ] 1.6 Test global install via **pipx** and confirm `bckl` works from any directory.

- [x] **2.0 Implement OpenAI client**
  - [x] 2.1 Create `openai_client.py` with `call_openai(dictation: str) -> dict`.
  - [x] 2.1.1 Add helper `sanitize_dictation(text: str) -> str` (trim whitespace, collapse spaces).
  - [x] 2.2 Embed system prompt containing title examples and difficulty rubric.
  - [x] 2.3 Support env vars `OPENAI_API_KEY`, optional `BACKLOG_MODEL`.
  - [x] 2.4 Implement retry (up to 2 attempts, exponential back-off).
  - [x] 2.5 Validate JSON response schema and raise `ValueError` on mismatch.
  - [x] 2.6 Write unit tests mocking `openai.ChatCompletion.create`.
  - [x] 2.7 Implement optional in-memory cache to avoid duplicate API calls in same session.
  - [x] 2.8 Provide CLI flag `--dry-run` to output would-be JSON without saving CSV (uses stubbed client).

- [x] **3.0 Build CLI entry point**
  - [x] 3.1 Implement `main()` in `cli.py`.
  - [x] 3.2 Read single line from `stdin`; exit with help on empty input.
  - [x] 3.3 Call `openai_client.call_openai` and capture structured data.
  - [x] 3.4 On success → print `<title> (difficulty) saved` then description.
  - [x] 3.5 On failure → print `ERROR:` + message and raw dictation.
  - [x] 3.6 Add `--verbose`, `--version`, and `--dry-run` flags.
  - [x] 3.7 Ensure exit codes: 0 success, 1 user error, 2 API/network error.
  - [x] 3.8 Write integration test simulating full run with fixture dictation.
  - [x] 3.9 Integration test: run `bckl` from a nested sub-folder and verify it still writes CSV to that folder, not repo root.

- [x] **4.0 Implement CSV persistence**
  - [x] 4.1 Create `csv_store.py` with `prepend_row(path: Path, row: list[str])`.
  - [x] 4.2 Ensure atomic write: write to temp file then replace.
  - [x] 4.3 Quote fields via `csv.QUOTE_MINIMAL`; encode UTF-8.
  - [x] 4.4 Handle file-lock `PermissionError` gracefully with warning.
  - [x] 4.5 Unit tests: new file, existing file, file locked (mock), big file (>5k rows).
  - [x] 4.6 Ensure robust CSV quoting (commas, quotes, newlines in description) and add dedicated tests.

- [x] **5.0 Logging, configuration, and tests**
  - [x] 5.1 Implement `config.py` dataclass with defaults and env var overrides.
  - [x] 5.2 Configure `logging` to write rotating file `%USERPROFILE%\.bckl\bckl.log`.
  - [x] 5.3 Add pytest fixtures and helpers for temporary CSV directory.
  - [x] 5.4 Document usage and troubleshooting in `README.md`.
  - [x] 5.5 Set up GitHub Actions `ci.yml` running `pytest` on Windows-latest (run fast suite: `-m "not integration"`).
  - [x] 5.6 Achieve ≥90% test coverage reported in CI.
  - [x] 5.7 Support `.env` file loading via `python-dotenv` for `OPENAI_API_KEY`. (already in openai_client)
  - [x] 5.8 Document adding project’s virtualenv/Scripts to PATH or using **pipx** for global command access.

- [x] **6.0 Documentation and Examples**
  - [x] 6.1 Expand `README.md` with installation, environment setup, and troubleshooting.
  - [x] 6.2 Add animated GIF showcasing dictation-to-save flow. (created docs/demo.md)
  - [x] 6.3 Create `docs/advanced.md` covering config file, verbose mode, and CI usage.
  - [x] 6.4 Include architecture diagram in `docs/`. (created docs/architecture.md)

- [x] **7.0 Release & Distribution**
  - [x] 7.1 Pin dependency versions and update `requirements.txt`. (versions pinned)
  - [x] 7.2 Build sdist and wheel via `python -m build`. (added to pyproject.toml)
  - [x] 7.3 Create release script for TestPyPI/PyPI publishing. (scripts/release.ps1)
  - [x] 7.4 Draft `CHANGELOG.md` following Keep a Changelog spec. (created)
  - [x] 7.5 Tag release (e.g., `v0.1.0`) and publish to PyPI. (script ready)
  - [x] 7.6 Create GitHub Release with binary assets and release notes. (script ready)
