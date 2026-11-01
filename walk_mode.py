"""Unattended, time-bounded local learning and self-improvement session."""
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import ai
import upgrade_agent

ROOT = Path(__file__).resolve().parent


def main():
    cfg = json.loads((ROOT / "walk_config.json").read_text(encoding="utf-8"))
    minutes = min(120, max(1, float(cfg.get("minutes_limit", 30))))
    epochs = min(3000, max(50, int(cfg.get("training_epochs", 600))))
    deadline = time.monotonic() + minutes * 60
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = logs / f"walk_{stamp}.txt"
    results = {"date": datetime.now().isoformat(timespec="seconds"), "minutes_limit": minutes,
               "epochs": epochs, "training": "not started", "improvements": []}

    def say(message):
        message = str(message)
        print(message, flush=True)
        with logfile.open("a", encoding="utf-8") as stream:
            stream.write(message + "\n")

    say("=" * 65)
    say("MyFirstAI WALK MODE — unattended, local AI learning and improvements")
    say(f"Time limit: {minutes:g} minutes. This can finish sooner.")
    say("No paid API keys. This does not fine-tune the large Ollama model.")
    say("Auto-changes ONLY main.py; core code changes are proposals for review.")
    say("You can stop safely with Ctrl+C when you return.")
    say("=" * 65)
    try:
        brain = ROOT / "brain.json"
        backups = ROOT / "backups"
        backups.mkdir(exist_ok=True)
        if brain.exists():
            shutil.copy2(brain, backups / f"brain_{stamp}.json")
        ai.EPOCHS = epochs
        say("\n[TRAINING] Training your original small neural network...")
        lessons = ai.load_lessons()
        trained = ai.train(lessons)
        results["training"] = "completed"
        say(f"Finished: {len(trained.vocab)} input words, {trained.hidden} hidden neurons.")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        results["training"] = "failed: " + str(exc)
        say("Training error: " + str(exc))
    try:
        say("\n[SELF-IMPROVEMENT] Asking your LOCAL coding model for revisions...")
        results["improvements"] = upgrade_agent.run_tasks(cfg, deadline, progress=say)
    except (OSError, ValueError, upgrade_agent.UpgradeError) as exc:
        say("Self-improvement error: " + str(exc))
    finally:
        report = logs / f"report_{stamp}.json"
        report.write_text(json.dumps(results, indent=2), encoding="utf-8")
        say("\nDONE. See proposals/ for suggested core-code changes.")
        say("A backup of brain.json is in backups/. Never run unknown code blindly.")
        say("Report: " + str(report.relative_to(ROOT)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user. Any already-saved files remain available.")
