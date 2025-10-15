# /ops/sync_assistants.py
import os, json
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]
ORCH = REPO / "ai" / "orchestrator.yaml"
TABS = REPO / "ai" / "tabs"

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# Accept either name (you said you use ASST_ORCHESTRATOR_ID)
ASSISTANT_ID = os.environ.get("ASSISTANT_ID_ORCH") or os.environ["ASST_ORCHESTRATOR_ID"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def read_yaml(p: Path):
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}

def load_tabs():
    TABS.mkdir(parents=True, exist_ok=True)
    out = []
    for f in sorted(TABS.glob("*.yaml")):
        d = read_yaml(f)
        if isinstance(d, dict) and isinstance(d.get("intent"), str):
            out.append({
                "intent": d["intent"].strip(),
                "summary": d.get("summary", "").strip(),
                "inputs": d.get("inputs", {}),
                "output_schema": d.get("output_schema", {}),
                "rules": d.get("rules", []),
            })
    return out

def build_instructions():
    orch = read_yaml(ORCH)
    globals_block = "\n".join(f"- {rule}" for rule in orch.get("global_rules", []))
    tabs = load_tabs()

    lines = []
    lines.append("You are the LightSignal Orchestrator.")
    lines.append("")
    lines.append("GLOBAL RULES:")
    lines.append(globals_block or "- (none)")
    lines.append("")
    lines.append("TABS / INTENTS:")
    for t in tabs:
        lines.append(f"- intent: {t['intent']}")
        if t["summary"]:
            lines.append(f"  summary: {t['summary']}")
        if t["rules"]:
            lines.append("  rules:")
            for r in t["rules"]:
                lines.append(f"    - {r}")
    lines.append("")
    lines.append("When called, you will receive JSON with:")
    lines.append("- tab_spec: the YAML spec for the requested intent")
    lines.append("- context.profile, context.financials, context.input")
    lines.append("Return STRICT JSON only, following the tab's output_schema.")
    return "\n".join(lines)

def main():
    instructions = build_instructions()
    # Update the existing assistant with new instructions & model
    client.beta.assistants.update(
        assistant_id=ASSISTANT_ID,
        model=OPENAI_MODEL,
        instructions=instructions
    )
    # Write a small artifact for debugging
    out = REPO / "ai" / "assistant_sync_info.json"
    out.write_text(json.dumps({"updated": True, "assistant_id": ASSISTANT_ID}, indent=2), encoding="utf-8")
    print("Synced assistant", ASSISTANT_ID)

if __name__ == "__main__":
    main()
