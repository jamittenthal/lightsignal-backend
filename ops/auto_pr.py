#!/usr/bin/env python3
import os, json, subprocess, sys, re, pathlib
from typing import List, Dict
from openai import OpenAI

# Inputs from the workflow
ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY  = os.environ["ISSUE_BODY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
REPO        = os.environ["GITHUB_REPOSITORY"]  # owner/repo
BRANCH_NAME = f"auto/build-{ISSUE_NUMBER}"

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.1")
client = OpenAI(api_key=OPENAI_API_KEY)

ROOT = pathlib.Path(".").resolve()

SYSTEM_PROMPT = """You are a senior full-stack engineer working on LightSignal.
Goal: Generate minimal, clean, PRODUCTION-READY edits to implement the issue.
Constraints:
- Only output STRICT JSON with this schema:
{
  "summary": "one paragraph summary for the PR body",
  "checklist": ["item", "..."],
  "edits": [
    {
      "path": "relative/path/filename.ext",
      "action": "create|update",
      "content": "full file content (UTF-8)"
    }
  ]
}
Rules:
- Prefer editing existing files over creating many new ones.
- Keep styling consistent with project; do not introduce new libs unless necessary.
- Ensure frontend compiles and backend starts. Update tests if present.
- For AI tabs: ensure JSON returned matches ai/tabs/<intent>.yaml output_schema.
- If unsure about exact data, add TODO comments but keep app runnable.
"""

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def run(cmd, check=True):
    print("+", cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)
    return result.stdout

def get_repo_snapshot() -> Dict[str, str]:
    # Read a selection of files to give the model context (frontend, backend, ai)
    paths = []
    for pattern in [
        "ai/orchestrator.yaml",
        "ai/tabs/*.yaml",
        "backend/**/*.py",
        "backend/**/*.json",
        "frontend/**/*.*",
        "render.yaml",
        "vercel.json"
    ]:
        paths += [str(p) for p in ROOT.glob(pattern) if p.is_file()]
    # Limit to avoid overloading token budget
    paths = paths[:60]
    blobs = {}
    for p in paths:
        try:
            blobs[p] = ROOT.joinpath(p).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass
    return blobs

def ask_model(issue_title: str, issue_body: str, snapshot: Dict[str,str]) -> Dict:
    user = {
        "issue_title": issue_title,
        "issue_body": issue_body,
        "repo_files": snapshot
    }
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":json.dumps(user)}
        ]
    )
    # Extract JSON
    content = resp.output_text
    # Make sure it's JSON (strip code fences if any)
    m = re.search(r'\{.*\}', content, re.DOTALL)
    if not m:
        print("Model response not JSON:", content)
        raise SystemExit(1)
    return json.loads(m.group(0))

def write_edits(edits: List[Dict]):
    for e in edits:
        path = ROOT.joinpath(e["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        content = e["content"].rstrip("\n") + "\n"
        path.write_text(content, encoding="utf-8")
        print("Wrote", e["path"])

def main():
    # Create branch
    run(f"git checkout -b {BRANCH_NAME}", check=True)

    # Ask model for edits
    snapshot = get_repo_snapshot()
    plan = ask_model(ISSUE_TITLE, ISSUE_BODY, snapshot)

    # Apply edits
    write_edits(plan["edits"])

    # Commit and push
    run("git add -A")
    run(f'git commit -m "auto: {ISSUE_TITLE} (#{ISSUE_NUMBER})"')
    run(f"git push -u origin {BRANCH_NAME}")

    # Open PR via GitHub CLI (gh) already installed on Actions runners
    summary = plan.get("summary","Auto PR")
    checklist = "\n".join([f"- [ ] {i}" for i in plan.get("checklist",[])])
    body = f"{summary}\n\n**Checklist**\n{checklist}\n\nCloses #{ISSUE_NUMBER}"
    run(f'gh pr create --fill --base main --head {BRANCH_NAME} --title "{ISSUE_TITLE}" --body "{body}"')

    print("✅ Opened PR for", ISSUE_TITLE)

if __name__ == "__main__":
    main()
