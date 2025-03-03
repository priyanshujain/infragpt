#!/usr/bin/env python3
"""Launcher for InfraGPT."""

import sys
from ..main import cli, main

def main():
    """Entry point for console_scripts."""
    # Check if we're using the `--` special form to pass everything after as a prompt
    if len(sys.argv) > 1 and sys.argv[1] == "--":
        # Special case for "infragpt -- text"
        prompt = sys.argv[2:]
        sys.argv = [sys.argv[0]]  # Reset sys.argv
        main(prompt=prompt)
    else:
        # Normal CLI handling
        cli()

if __name__ == "__main__":
    main()