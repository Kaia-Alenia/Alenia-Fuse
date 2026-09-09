#!/usr/bin/env bash
set -euo pipefail

echo "Installing the Alenia Fuse distribution and the fuse command..."
command -v python3 >/dev/null 2>&1 || {
  echo "Python 3.11+ is required." >&2
  exit 1
}

python3 -m pip install alenia-fuse
echo "Installation complete. Run: fuse --help"
