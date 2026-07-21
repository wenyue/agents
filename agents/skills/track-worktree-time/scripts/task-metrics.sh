#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

for python_command in python3 python; do
  if command -v "$python_command" >/dev/null 2>&1 &&
    "$python_command" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'
  then
    exec "$python_command" "$script_dir/timing.py" "$@"
  fi
done

python_path=$(
  printf '%s\n' "${PATH:-}" |
    tr ':' '\n' |
    while IFS= read -r path_directory; do
      [ -n "$path_directory" ] || path_directory=.
      for python_candidate in "$path_directory"/python3.*; do
        [ -x "$python_candidate" ] || continue
        case "${python_candidate##*/}" in
          python3.[0-9] | python3.[0-9][0-9]) ;;
          *) continue ;;
        esac
        if "$python_candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'
        then
          printf '%s\n' "$python_candidate"
          break 2
        fi
      done
    done
)
if [ -n "$python_path" ]; then
  exec "$python_path" "$script_dir/timing.py" "$@"
fi

if command -v uv >/dev/null 2>&1; then
  python_command=$(uv python find '>=3.11')
  exec "$python_command" "$script_dir/timing.py" "$@"
fi

echo 'ERROR: Python 3.11 or newer is required.' >&2
exit 2
