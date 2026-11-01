"""Review self-improvement proposals and apply selected code with a backup."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import upgrade_agent

ROOT = Path(__file__).resolve().parent


def main():
    folder = ROOT / "proposals"
    options = sorted(folder.glob("*.candidate.py")) if folder.exists() else []
    if not options:
        print("No proposals yet. Run train.cmd once first.")
        return
    print("\nMyFirstAI — Review changes to its own code")
    print("NOTE: Syntax checks do not guarantee AI-generated code is safe.")
    for index, item in enumerate(options, 1):
        print(f"  {index:>2}. {item.name}")
    choice = input("\nProposal number (or Enter to exit): ").strip()
    if not choice:
        return
    if not choice.isdecimal() or not 1 <= int(choice) <= len(options):
        print("Invalid selection.")
        return
    candidate = options[int(choice) - 1]
    suffix_name = candidate.name.split("_", 3)[-1]  # 'main_py.candidate.py' etc
    match = {"main_py.candidate.py": "main.py", "ai_py.candidate.py": "ai.py",
             "smart_ai_py.candidate.py": "smart_ai.py"}
    target_name = match.get(suffix_name)
    if target_name is None:
        print("Unrecognized proposal name. Not applying.")
        return
    target = ROOT / target_name
    if target.is_symlink() or not target.is_file():
        print("Target is missing or linked. Not applying.")
        return
    updated = candidate.read_text(encoding="utf-8")
    current = target.read_text(encoding="utf-8")
    valid, reason = upgrade_agent.validate_candidate(target_name, current, updated)
    print("Check:", reason)
    if not valid:
        print("This proposal cannot be applied.")
        return
    diff_path = candidate.with_name(candidate.name.replace(".candidate.py", ".diff.txt"))
    if diff_path.is_file():
        print("\n--------- Proposed changes (first 12,000 characters) ---------")
        print(diff_path.read_text(encoding="utf-8")[:12000])
        print("--------- End preview ---------\n")
    confirm = input(f"Replace your {target_name}? Type APPLY to confirm: ").strip()
    if confirm != "APPLY":
        print("Canceled. No files changed.")
        return
    backup = ROOT / "backups"
    backup.mkdir(exist_ok=True)
    destination = backup / (datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + target_name.replace(".", "_") + ".backup.py")
    shutil.copy2(target, destination)
    target.write_text(updated, encoding="utf-8")
    print("Applied:", target_name)
    print("Backup:", destination.relative_to(ROOT))
    print("Restart start.cmd to pick up changes. Review any code you run.")


if __name__ == "__main__":
    main()
