# ai_registry.py
import os, glob, yaml, time
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TABS = BASE_DIR / "ai" / "tabs"
AI_TABS_DIR = Path(os.environ.get("AI_TABS_DIR", str(DEFAULT_TABS)))

_cache: Dict[str, Any] = {
    "by_intent": {},
    "last_scan": 0.0,
    "files": []
}
_SCAN_INTERVAL = 5.0  # seconds

def _scan_files() -> None:
    AI_TABS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(AI_TABS_DIR / "*.yaml")))
    _cache["files"] = files

def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _refresh_cache_if_needed() -> None:
    now = time.time()
    if now - _cache["last_scan"] < _SCAN_INTERVAL:
        return
    _cache["last_scan"] = now

    _scan_files()
    by_intent: Dict[str, Dict[str, Any]] = {}
    for path in _cache["files"]:
        try:
            spec = _load_yaml(path)
            intent = spec.get("intent")
            if isinstance(intent, str) and intent.strip():
                by_intent[intent.strip()] = spec
        except Exception:
            # ignore malformed files
            pass
    _cache["by_intent"] = by_intent

def list_intents() -> List[str]:
    _refresh_cache_if_needed()
    return sorted(_cache["by_intent"].keys())

def get_tab_spec(intent: str) -> Optional[Dict[str, Any]]:
    _refresh_cache_if_needed()
    return _cache["by_intent"].get(intent)
