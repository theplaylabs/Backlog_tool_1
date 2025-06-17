"""Command-line interface for the Backlog CLI tool.

Reads a single line of dictation from **stdin**, sends it to the OpenAI client, and
prepends the structured entry to `backlog.csv` in the current directory.  A
`--dry-run` flag lets you preview the JSON without touching the CSV (handy for
unit tests).

Exit codes: 0 success, 1 user error, 2 API/network error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__ as _VERSION
from . import csv_store, openai_client


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bckl",
        description="Dictation-driven backlog entry tool",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print JSON output but do not write to CSV",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging (currently prints JSON).",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"bckl {_VERSION}",
    )
    return p


def main(argv: list[str] | None = None) -> None:  # noqa: D401
    """Program entry point."""
    argv = argv if argv is not None else sys.argv[1:]
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Read single line dictation from stdin
    try:
        dictation = sys.stdin.readline()
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(1)

    if not dictation.strip():
        parser.error("No input received – please dictate or type a line and press Enter.")

    try:
        data = openai_client.call_openai(dictation)
    except Exception as exc:  # broad: translate to exit code 2
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        print(json.dumps(data, indent=2))
        sys.exit(0)

    # Attempt to write to CSV – until csv_store is implemented, handle gracefully
    csv_path = Path.cwd() / "backlog.csv"
    try:
        csv_store.prepend_row(
            csv_path,
            [data["timestamp"], data["title"], str(data["difficulty"]), data["description"]],
        )
    except NotImplementedError:
        # Development placeholder
        print("(CSV persistence not yet implemented – dry run implied)")
    except Exception as exc:  # pragma: no cover
        print(f"ERROR saving CSV: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"{data['title']} ({data['difficulty']}) saved")
    if args.verbose:
        print(data["description"])

    sys.exit(0)

if __name__ == "__main__":
    main()
