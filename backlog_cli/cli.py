"""Command-line interface for the Backlog CLI tool.

Reads a single line of dictation from **stdin**, sends it to the OpenAI client, and
prepends the structured entry to `backlog.csv` in the current directory.  A
`--dry-run` flag lets you preview the JSON without touching the CSV (handy for
unit tests).

Exit codes:
    0: Success
    1: User error (invalid input, keyboard interrupt)
    2: API/network/file error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__ as _VERSION
from . import csv_store, openai_client, config


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
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
    """Program entry point.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])
    """
    # Process command-line arguments
    argv = argv if argv is not None else sys.argv[1:]
    parser = _build_parser()

    # Ensure logging configured early
    logger = config.get_logger(__name__)
    args = parser.parse_args(argv)

    # Read single line dictation from stdin
    try:
        dictation = sys.stdin.readline()
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(1)

    # Validate input
    if not dictation.strip():
        parser.error("No input received – please dictate or type a line and press Enter.")

    # Process dictation through OpenAI
    try:
        data = openai_client.call_openai(dictation)
    except Exception as exc:  # broad: translate to exit code 2
        logger.error(f"OpenAI API error: {exc}")
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    # Handle dry run mode
    if args.dry_run:
        print(json.dumps(data, indent=2))
        logger.info("Dry-run output for dictation: %s", dictation.strip())
        sys.exit(0)

    # Interactive editing loop
    while True:
        # Display the current entry
        print()  # Empty line for readability
        print(f"Title: {data['title']}")
        print(f"Difficulty: {data['difficulty']}")
        print(f"Description: {data['description']}")
        print()  # Empty line for readability
        
        # Prompt for edits (blank line to accept)
        try:
            print("> ", end="", flush=True)  # Show prompt for edit instructions
            edit_instructions = sys.stdin.readline().strip()
        except KeyboardInterrupt:
            print("\nCancelled.", file=sys.stderr)
            sys.exit(1)
            
        # If no edit instructions provided, proceed with saving
        if not edit_instructions:
            break
            
        # Process edit instructions through OpenAI
        try:
            data = openai_client.edit_backlog_entry(data, edit_instructions)
            logger.info("Entry updated based on edit instructions")
        except Exception as exc:
            logger.error(f"Error processing edit instructions: {exc}")
            print(f"ERROR: {exc}", file=sys.stderr)
            print("Original entry preserved. You can try different edit instructions.")
            # Continue the loop with the original data

    # Prepare CSV file
    csv_path = Path.cwd() / "backlog.csv"
    
    # Create empty file if it doesn't exist
    if not csv_path.exists():
        logger.info("Creating new backlog.csv file")
        try:
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                pass  # Just create an empty file
        except Exception as exc:
            logger.error(f"Failed to create CSV file: {exc}")
            print(f"ERROR creating CSV file: {exc}", file=sys.stderr)
            sys.exit(2)
    
    # Write data to CSV
    try:
        csv_store.prepend_row(
            csv_path,
            [data["title"], str(data["difficulty"]), data["description"], data["timestamp"]],
        )
    except NotImplementedError:
        # Development placeholder
        logger.warning("CSV persistence not implemented")
        print("(CSV persistence not yet implemented – dry run implied)")
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to save to CSV: {exc}")
        print(f"ERROR saving CSV: {exc}", file=sys.stderr)
        sys.exit(2)

    # Display simple confirmation
    print(f"Entry saved: {data['title']} (difficulty: {data['difficulty']})")
    
    
    # Log success
    logger.info("Entry saved: %s", data['title'])

    sys.exit(0)

if __name__ == "__main__":
    main()
