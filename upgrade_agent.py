"""Local self-improvement planner. No new modules, keys, or cloud services.

The local Ollama coding model proposes revisions. ONLY a guarded main.py
launcher can be auto-applied. Revisions to the actual AI engine are saved as
patch proposals for the owner to review. Generated scripts are never run.
"""
from __future__ import annotations

import ast
import difflib
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parent
ALLOWED_TARGETS = {"main.py", "ai.py", "smart_ai.py"}
MAX_SOURCE = 45_000
MAX_REPLY = 85_000
MODEL_URL = "http://127.0.0.1:11434/api/chat"
PREVIEW_DIR = ROOT / "proposals"
BACKUP_DIR = ROOT / "backups"


class UpgradeError(Exception):
    pass


def ask_model(model: str, filename: str, goal: str, original: str, timeout: int = 180) -> str:
    """Call Ollama's LOCAL chat API; never send source to a cloud service."""
    if len(original) > MAX_SOURCE:
        raise UpgradeError(f"{filename} is too long for this local improvement job.")
    prompt = (
        f"You are revising your own local Python program, file: {filename}.\n"
        f"One improvement goal: {goal}\n"
        "Return the COMPLETE updated Python file (not a diff or Markdown).\n"
        "Rules: Keep existing public behavior, APIs, security checks, and CLI usage. "
        "Use Python 3 standard library only. Do not run anything, access other files "
        "or networks, or add new dependencies. Do not remove important code. "
        "If you are unable to safely improve it, return the original source unchanged.\n\n"
        "===== BEGIN ORIGINAL SOURCE =====\n" + original + "\n===== END ORIGINAL SOURCE ====="
    )
    payload = {"model": model, "stream": False,
               "messages": [{"role": "system", "content": "You are a careful Python maintenance programmer. Output only complete code."},
                            {"role": "user", "content": prompt}],
               "options": {"temperature": 0.1, "num_predict": 5500}}
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(MODEL_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read(MAX_REPLY)
    except (OSError, TimeoutError, error.URLError) as exc:
        raise UpgradeError("Local Ollama isn't responding. Open Ollama and run setup_smart.cmd first.") from exc
    try:
        answer = json.loads(raw)["message"]["content"].strip()
    except (ValueError, TypeError, KeyError) as exc:
        raise UpgradeError("Ollama sent an unexpected response.") from exc
    if answer.startswith("```"):
        lines = answer.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            answer = "\n".join(lines[1:-1])
    return answer.rstrip() + "\n"


def validate_candidate(filename: str, original: str, candidate: str) -> tuple[bool, str]:
    """Syntax checks; this is NOT a guarantee that AI-generated code is safe."""
    if filename not in ALLOWED_TARGETS:
        return False, "Target not in allowed source file list."
    if not candidate.strip() or len(candidate.encode("utf-8")) > MAX_REPLY:
        return False, "Empty or oversized model output."
    if candidate == original:
        return False, "No changes proposed."
    try:
        tree = ast.parse(candidate, filename)
        compile(candidate, filename, "exec")  # compile ONLY; do not run model-generated code
    except (SyntaxError, ValueError) as exc:
        return False, f"Python syntax error: {exc}"
    if filename == "main.py":
        # Permit auto-apply ONLY to the small startup wrapper and only if it
        # retains the intended code path and no suspect imports/calls appear.
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add((node.module or "").split('.')[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__", "compile", "open"}:
                return False, "Launcher uses dynamic code execution or file access."
        # Only imports used by the original launcher should be needed.
        if imports != {"smart_ai"}:
            return False, "Launcher imported something new; requires manual review."
        if "start_browser" not in candidate or "def main(" not in candidate:
            return False, "Launcher no longer contains the expected entry point."
        if any(isinstance(n, (ast.Delete, ast.Global, ast.Nonlocal)) for n in ast.walk(tree)):
            return False, "Unexpected code construct in launcher."
    return True, "Python syntax OK. Generated code has NOT been executed."


def job(filename: str, goal: str, model: str, auto_apply_main_only: bool, *, ask=ask_model) -> dict:
    if filename not in ALLOWED_TARGETS:
        raise UpgradeError("Only main.py, ai.py and smart_ai.py may be edited by the agent.")
    if not isinstance(goal, str) or len(goal) > 1000:
        raise UpgradeError("Invalid task.")
    target = ROOT / filename
    if not target.is_file() or target.is_symlink() or target.stat().st_size > MAX_SOURCE:
        raise UpgradeError(f"Can't safely open {filename}.")
    original = target.read_text(encoding="utf-8")
    candidate = ask(model, filename, goal, original)
    valid, reason = validate_candidate(filename, original, candidate)
    if not valid:
        return {"file": filename, "status": "skipped", "reason": reason}

    PREVIEW_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = f"{timestamp}_{filename.replace('.', '_')}"
    proposal_path = PREVIEW_DIR / (stem + ".candidate.py")
    diff_path = PREVIEW_DIR / (stem + ".diff.txt")
    proposal_path.write_text(candidate, encoding="utf-8")
    diff_text = "".join(difflib.unified_diff(
        original.splitlines(keepends=True), candidate.splitlines(keepends=True),
        fromfile="original/" + filename, tofile="proposed/" + filename))
    diff_path.write_text(diff_text, encoding="utf-8")
    result = {"file": filename, "status": "proposal", "candidate": str(proposal_path.relative_to(ROOT)),
              "diff": str(diff_path.relative_to(ROOT)), "reason": reason}

    # Self-rewrite the launcher as explicitly requested, but DO NOT execute it.
    # Keep a restorable backup. The main AI engine requires review.
    if filename == "main.py" and auto_apply_main_only:
        backup_path = BACKUP_DIR / (stem + ".backup.py")
        backup_path.write_text(original, encoding="utf-8")
        target.write_text(candidate, encoding="utf-8")
        result.update(status="applied_to_main", backup=str(backup_path.relative_to(ROOT)))
    return result


def load_tasks() -> list[dict]:
    data = json.loads((ROOT / "improve_tasks.json").read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise UpgradeError("improve_tasks.json must contain a JSON list.")
    tasks = []
    for entry in data:
        if not isinstance(entry, dict) or entry.get("file") not in ALLOWED_TARGETS or not isinstance(entry.get("goal"), str):
            raise UpgradeError("Task must have an allowed 'file' and text 'goal'.")
        tasks.append(entry)
    return tasks


def run_tasks(config: dict, deadline: float, *, progress=print) -> list[dict]:
    count = max(0, min(6, int(config.get("max_tasks", 3))))
    model = str(config.get("ollama_model", "qwen2.5-coder:3b"))
    results = []
    tasks = load_tasks()[:count]
    for i, entry in enumerate(tasks, 1):
        if time.monotonic() >= deadline:
            progress("Time limit reached. Ending safely.")
            break
        remaining = deadline - time.monotonic()
        if remaining < 15:
            progress("Not enough time for another proposal.")
            break
        progress(f"\n[{i}/{len(tasks)}] AI is proposing improvements to {entry['file']}...")
        try:
            # Keep calls time-bounded; total session may finish sooner than deadline.
            def timed_ask(model, filename, goal, original):
                return ask_model(model, filename, goal, original, timeout=min(180, max(10, int(remaining))))
            record = job(entry["file"], entry["goal"], model,
                         bool(config.get("auto_apply_main_only", True)), ask=timed_ask)
        except (UpgradeError, OSError, ValueError) as exc:
            record = {"file": entry["file"], "status": "error", "reason": str(exc)}
        results.append(record)
        progress(f"Result: {record['status']} — {record.get('reason', '')}")
    return results
