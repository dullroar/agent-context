#!/usr/bin/env bash
set -u
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'setup: Python 3.10 or newer is required.' >&2
  exit 1
fi
exec python3 "$script_dir/setup.py" "$@"
