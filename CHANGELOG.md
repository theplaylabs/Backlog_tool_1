# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Configuration system with env var overrides.
- Rotating-file logging to `%USERPROFILE%\.bckl`.
- Comprehensive test suite with selective markers (`new`, `integration`).
- GitHub Actions workflow for CI with coverage gate (≥90%).
- Advanced usage guide in `docs/advanced.md`.

### Changed
- Default OpenAI model set to `gpt-4o-mini`.

## [0.1.0] - 2025-06-17
### Added
- Initial CLI (`bckl`) parsing dictation, calling OpenAI, writing `backlog.csv`.
- OpenAI client with retry and schema validation.
- Atomic CSV prepend functionality.
- Offline test stubs and full suite of unit/integration tests.
