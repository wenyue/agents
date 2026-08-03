#!/bin/sh

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$script_dir/check_recommended_tools.py" "$@"
status=$?
if [ "$1" = "hook" ]; then
  exit 0
fi
exit "$status"
