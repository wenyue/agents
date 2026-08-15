import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source.json"
OUTPUT = ROOT / "data" / "catalog.json"


def load(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise SystemExit(2)
    if not isinstance(value, dict) or not isinstance(value.get("items"), list):
        raise SystemExit(2)
    return value


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"check", "build"}:
        raise SystemExit(2)
    source = load(SOURCE)
    if sys.argv[1] == "check":
        output = load(OUTPUT)
        raise SystemExit(0 if output == source else 3)
    OUTPUT.write_text(json.dumps(source, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
