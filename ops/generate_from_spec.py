# /ops/generate_from_spec.py
import json, re
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]
TABS_DIR = REPO / "ai" / "tabs"
INDEX = REPO / "ai" / "index.json"

def slug_to_intent(path: Path) -> str:
    # example: financial_overview.yaml -> financial_overview
    return path.stem.strip()

def ensure_intent_field(path: Path) -> bool:
    """
    Ensure YAML has top-level `intent:`. If missing, add it from filename.
    Returns True if file was modified.
    """
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except Exception:
        data = None

    if not isinstance(data, dict):
        # Create a minimal spec if the file was empty/invalid
        data = {}

    changed = False
    if not isinstance(data.get("intent"), str) or not data["intent"].strip():
        data["intent"] = slug_to_intent(path)
        changed = True

    # Keep file content stable & readable
    new_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        changed = True
    return changed

def build_index(files):
    intents = []
    for p in files:
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            intent = data.get("intent") or slug_to_intent(p)
            if isinstance(intent, str) and intent.strip():
                intents.append(intent.strip())
        except Exception:
            pass
    intents = sorted(set(intents))
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps({"intents": intents}, indent=2), encoding="utf-8")
    return intents

def main():
    if not TABS_DIR.exists():
        print("No ai/tabs directory found, nothing to do.")
        return 0
    files = sorted(TABS_DIR.glob("*.yaml"))
    touched = False
    for f in files:
        if ensure_intent_field(f):
            print(f"Updated: {f}")
            touched = True
    intents = build_index(files)
    print("Intents:", intents)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
