# Backlog CLI Tool PRD

> **Status:** Draft v0.2 – awaiting stakeholder review
>
> **Owner:** Developer / Product Lead (user)
> **Date:** 2025-06-17

---

## 1. Introduction / Overview
The **Backlog CLI Tool** (`bckl`) is a lightweight command-line companion that lets a developer dictate feature ideas, bug fixes, or technical-debt items and have them instantly appended—**at the top**—of a project-local `backlog.csv`. Leveraging an OpenAI chat completion, the tool:

1. Repairs common dictation issues (capitalisation, punctuation, homophones).
2. Distils the spoken text into a concise 5–6-word **git-style title** and a cleaned **description**.
3. Estimates feature **difficulty** on a 1–5 scale using a consistent rubric.
4. Persists the entry to `backlog.csv` in **the directory from which the command is executed**—never in the tool’s install directory—ensuring each repository maintains its own backlog.

The goal is to remove the friction of backlog grooming so that ideas are captured in seconds rather than forgotten or recorded inconsistently.

---

## 2. Goals & Objectives
1. **Seamless Capture** – Speak → press Enter → item saved; total round-trip ≤ 5 s.
2. **High-Quality Formatting** – ≥ 95 % of entries conform to title/description guidelines without manual editing.
3. **Reliable Difficulty Estimation** – Difficulty rating within ±1 of human judgment 90 % of the time.
4. **Local Autonomy** – Each project keeps its own `backlog.csv` at repository root; no global or centralised storage.
5. **Zero Data Loss** – On API failure, raw dictation printed so it can be copied; CSV never corrupted.

---

## 3. Glossary
* **Dictation** – Voice-to-text transcription captured by the OS and piped into `bckl`.
* **CWD** – Current Working Directory, the folder in which the user runs the command; equals the repository root for this tool.
* **Entry** – A single backlog row: Title, Difficulty, Description, Timestamp.

---

## 4. Title Guidelines
The title must read like an imperative git commit and convey the essence of the feature in **5–6 words**.

Good examples | Why they’re good
-------------- | ----------------
`Add OAuth login flow` | Verb + noun, clear scope.
`Refactor payment adapter module` | Signals internal change.
`Improve CSV import performance` | Indicates metric (performance).

Bad examples | Issue
-------------|------
`oauth` | Too vague.
`We should maybe change the thing` | Non-imperative, filler words.
`Fix bug in code` | Lacks specificity.

The OpenAI prompt will embed these examples so the model can mimic the desired pattern.

---

## 5. Difficulty Rubric
Score | Definition | Typical Effort
----- | ---------- | --------------
1 | Tiny tweak | ≤ 30 min; one-liner or comments.
2 | Small feature | 0.5–2 h; touches single file.
3 | Medium feature | 0.5–1 day; multiple files/functions.
4 | Large feature | 1–3 days; refactor or new subsystem.
5 | Complex new module | >3 days; cross-cutting impact, new infrastructure.

The rubric text is embedded verbatim in the system prompt to ensure consistent scoring.

---

## 6. Detailed Functional Requirements
1. **Input Handling**
   1. Read **stdin** until the first newline (single-line dictation).
   2. Empty input → display help and exit with non-zero code.
2. **Prompt Construction**
   1. System message: _“You are a backlog assistant…”_ including title examples & rubric.
   2. User message: raw dictation.
3. **OpenAI Invocation**
   1. Model default `gpt-3.5-turbo`; override via `BACKLOG_MODEL` env var.
   2. Temperature 0.3 for determinism.
4. **Response Validation**
   1. Parse JSON. Fields: `title:str`, `difficulty:int(1-5)`, `description:str`, `timestamp:str(ISO-8601)`.
   2. Re-prompt once on schema errors; if still invalid → error flow.
5. **CSV Persistence**
   1. Filename fixed: `backlog.csv`.
   2. Location: **Path.cwd() / "backlog.csv"**.
   3. New row written **before** existing rows (prepend). Handle file creation.
   4. CSV encoded UTF-8 with quoting via `csv.writer(quoting=csv.QUOTE_MINIMAL)`.
6. **Console Output**
   1. On success: `<title> (difficulty) saved` newline `description`.
   2. On failure: `ERROR: <reason>` newline raw dictation.
7. **Invocation & Packaging**
   1. Installed with `pip install .`; `setup.cfg` exposes `console_scripts = bckl=backlog_cli.cli:main`.
   2. Requires Python ≥ 3.9; Windows 10+.

---

## 7. Non-Functional Requirements
* **Performance:** API round-trip <4 s p95.
* **Reliability:** Tool must not crash on empty or >2 KB input.
* **Security:** No dictation text or CSV content is logged remotely.
* **Portability:** Operates offline (except API call) in any Git Bash / PowerShell.

---

## 8. Error Handling & Edge Cases
Scenario | Expected Behaviour
---------|-------------------
OpenAI network timeout | Retry up to 2× with exponential backoff; then fall back to error flow.
CSV locked by another process | Print warning, skip write, keep dictation visible.
Title duplicates existing entry | Allowed; tool does not enforce uniqueness.
Input length >2 KB | Truncate with ellipsis before sending to API; note truncation in description.

---

## 9. Success Metrics
1. **Formatting Accuracy:** ≥ 95 % of titles pass automated regex `^[A-Z][a-z]+( [A-Z][a-z]+){1,5}$` (capitalised words, 2–6).  
2. **Difficulty Consistency:** Human audit of 50 items shows ≤ 10 mis-scores.
3. **User Adoption:** ≥ 10 backlog items/week added via CLI over a rolling 4-week window.
4. **Reliability:** <1 % of invocations result in error flow (excluding network outages).

---

## 10. Design & Implementation Notes
* **CSV Prepend Technique:** Read entire file into memory (files <1 MB typical) → write new file with row + previous content; atomic replace.
* **Logging:** Optional `--verbose` flag writes a rotating log at `.bckl\bckl.log` for debugging.
* **Extensibility:** Architecture isolates: _cli.py_ (IO) | _openai_client.py_ | _csv_store.py_ for easy testing & future web UI.

---

## 11. Future Enhancements (Out of Scope for v1)
1. Multi-line dictation or “stop recording” hotkey.
2. Interactive query mode: filter backlog by difficulty/time.
3. Web dashboard for prioritisation.
4. Automatic duplicate detection and merging.

---

## 12. Open Questions
1. Should the tool optionally auto-open the CSV in Excel after save?
2. Do we want a configuration file (e.g., `.bckl.toml`) for per-repo overrides (model, rubric, file name)?
3. What testing framework/version matrix is required for CI on Windows?

---

## 13. Risks & Mitigations
Risk | Impact | Mitigation
---- | ------- | ----------
OpenAI pricing spike | Cost overrun | Allow model override + local fallback summariser.
Dictation mis-transcription | Incorrect backlog items | Encourage quick manual review via immediate terminal echo.
CSV merge conflicts in Git | Data loss | Prepend ensures chronological clarity; recommend CSV-friendly merge driver.

---

## 14. Approval
| Role | Name | Decision |
|------|------|----------|
| Product Lead | *TBD* |  |
| Developer | *TBD* |  |

---

**Next Steps** — Gather feedback, finalise PRD, then proceed to architectural design & implementation plan.
