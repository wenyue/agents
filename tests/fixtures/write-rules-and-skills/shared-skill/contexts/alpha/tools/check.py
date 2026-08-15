import sys

SUPPORTED = {"unit", "format"}

if len(sys.argv) != 2 or sys.argv[1] not in SUPPORTED:
    raise SystemExit(2)
raise SystemExit(0)
