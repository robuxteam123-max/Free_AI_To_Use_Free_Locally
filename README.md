# MyFirstAI Smart — Walk Mode + Self-Improvement

**Works on Windows with `py`**. This is an upgrade of MyFirstAI Smart; your original neural network is still included.

## What it does

- **`start.cmd`** launches a browser coding assistant at http://127.0.0.1:8765 using a local, pretrained coding model through Ollama. It can write HTML, JS, CSS, and Python. The browser's Build/Edit feature still requires your approval before saving into `workspace/`.
- **`train.cmd`** runs a *bounded, unattended session*. It does actual backpropagation training on your original 18-neuron neural network, saving `brain.json`, and then asks Ollama for possible improvements to its own source code.
- **Auto-update:** The improvement agent can automatically rewrite the little entrypoint **`main.py`**, keeping a timestamped backup. It **does not execute the generated code while unattended**. If a proposed change is not valid Python, it is skipped. Automatic upgrades to `ai.py` and `smart_ai.py` are **disabled by design**; those are staged as reviewable proposals.
- **`review_upgrades.cmd`** lets you preview and select a proposal to apply to the *core* source files, with an automatic backup. The generated changes might still have bugs or security issues, so inspect them.
- **`restore_main.cmd`** restores the most recent backed-up `main.py` if its edited launcher stops working.
- All of this runs **locally with no Gemini or OpenAI API keys**. Ollama requires a one-time model download but no API key. The local model is not being retrained or fine-tuned by `train.cmd`.

## Setup, simple steps

1. Extract this ZIP. Keep its folder together.
2. Install Python 3 with the Windows `py` launcher (if missing): https://www.python.org/downloads/
3. Install/open Ollama: https://ollama.com/download/windows
4. Run **`setup_smart.cmd`** once. This downloads `qwen2.5-coder:3b` (~1.9 GB). You need the internet for that download.
5. Run **`start.cmd`** to chat with your AI.
6. Close the AI or leave it open, then double-click **`train.cmd`** when you want it to train and propose self-improvements while you're away.
7. When back, read the on-screen report and look inside `logs/` and `proposals/`. Run **`review_upgrades.cmd`** to decide whether to apply core changes.

**Leaving it running:** Keep the PC awake and plugged in, and keep Ollama open. The AI only runs while Windows is awake; closing the CMD window stops it. `train.cmd` may finish well before the 30-minute cap. It does not need you to sit there, and it can stop by itself after its task limit is reached. Do not expect it to get infinitely smarter just by repeating the same lessons.

## Customize Walk Mode

Open **`walk_config.json`** with VS Code or Notepad:

```json
{
  "minutes_limit": 30,
  "max_tasks": 3,
  "training_epochs": 600,
  "ollama_model": "qwen2.5-coder:3b",
  "auto_apply_main_only": true
}
```

- `minutes_limit`: a **maximum**, from 1 to 120 minutes (not a promise that the session runs the full time).
- `max_tasks`: maximum improvement proposals, from 0 to 6.
- `training_epochs`: how many times the *small from-scratch model* learns from the lessons, from 50 to 3,000.
- `auto_apply_main_only`: set to `false` if you want **all** suggested changes held for your review. This cannot enable unattended rewrites to core source files.
- `ollama_model`: any downloaded Ollama model name; larger models may give better coding suggestions and use more memory.

Edit **`improve_tasks.json`** to set goals for the self-improvement engine. It accepts goals targeting `main.py`, `ai.py`, or `smart_ai.py` only; it never executes arbitrary generated commands or scripts.

## How learning actually works

There are **two different types of change**, and they should not be confused:

1. **Small original neural network** (`ai.py` and `brain.json`): real training by backpropagation on `lessons.json`. New lessons can improve it. Running more epochs on unchanged examples will eventually stop improving it. It is not ChatGPT.
2. **Smart Mode (`qwen2.5-coder:3b`)**: pretrained local language model used to write and revise code. `train.cmd` **does not** modify this model's weights. To truly fine-tune an LLM, you need a different, more demanding training pipeline and substantial example data.

## Important safety and limitations

- AI-generated code **can be incorrect or dangerous**. Python syntax validation is not a full security scan or a guarantee the updated program works. Always review modified `main.py` before restarting `start.cmd`.
- The agent is confined to an allowlist of this project's Python files for improvements and uses `http://127.0.0.1:11434` for local inference. It cannot install software or freely access Windows commands as a tool.
- Backups are saved in `backups/`, human-readable improvement suggestions in `proposals/`, and reports in `logs/`.
- The `start.cmd` browser app cannot edit its own core code through the browser. It still writes only under `workspace/` when you approve.
- The program is not an unrestricted autonomous AI. It will not invent new training data on its own or become as capable as the latest cloud models by running overnight.
- If `train.cmd` reports Ollama unavailable, your original small AI still trains, but self-improvement proposals require Ollama.
- Run `test_all.cmd` to check basic code paths, or run `py -m unittest discover -p "test_*.py" -v` in Command Prompt.
