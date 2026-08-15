import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "schema" / "api.json"
OUTPUT = ROOT / "src" / "generated" / "client.txt"

try:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    service = source["service"]
except (OSError, json.JSONDecodeError, KeyError, TypeError):
    raise SystemExit(2)

expected = f"client:{service}\n"
try:
    actual = OUTPUT.read_text(encoding="utf-8")
except OSError:
    raise SystemExit(2)
raise SystemExit(0 if actual == expected else 2)
