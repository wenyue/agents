import sys

if len(sys.argv) != 2:
    raise SystemExit(2)
if sys.argv[1] == "schema":
    raise SystemExit(0)
if sys.argv[1] == "integration":
    raise SystemExit(4)
raise SystemExit(2)
