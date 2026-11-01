"""MyFirstAI Smart — local coding assistant, standard-library Python web server.

The original from-scratch neural network is still in ai.py. Smart Mode calls
an OPTIONAL, pretrained language model via Ollama on 127.0.0.1; no API key.
No model files or Python packages are included in this project.
"""
from __future__ import annotations

import json
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request, error
from urllib.parse import urlsplit
import webbrowser

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
WEBPAGE = ROOT / "index.html"
HOST = "127.0.0.1"
OLLAMA = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5-coder:3b"
ALLOWED_EXTENSIONS = {".py", ".html", ".htm", ".css", ".js", ".mjs", ".ts", ".jsx", ".tsx", ".json", ".md", ".txt", ".svg", ".xml", ".csv"}
MAX_INPUT = 1024 * 1024
MAX_FILE = 256 * 1024

SYSTEM_PROMPT = """You are MyFirstAI Smart, a helpful local AI coding assistant.
Give useful answers, generate complete runnable code when asked, and explain
steps in beginner-friendly language. Do not claim you executed code, edited a
file, used the internet, or tested anything unless you actually did so.
The user operates Windows and launches Python with `py` (not `python`).
If something is uncertain, be transparent about limitations."""

class AppError(Exception):
    pass


def workspace_path(filename: str) -> Path:
    """Allow editing only conventional text/code files inside workspace."""
    if not isinstance(filename, str) or not filename.strip() or len(filename) > 180:
        raise AppError("Enter a short filename such as index.html or app.py.")
    rel = Path(filename.replace("\\", "/"))
    if rel.is_absolute() or rel.drive or any(part in (".", "..") for part in rel.parts):
        raise AppError("Files must be inside the workspace folder.")
    if len(rel.parts) > 5 or rel.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise AppError("Use a supported code/text extension, such as .py, .html, .js or .css.")
    if any(part.startswith(".") or ":" in part or (Path(part).suffix and part != rel.name) for part in rel.parts):
        raise AppError("Hidden files and special paths aren't supported.")
    root = WORKSPACE.resolve()
    target = (root / rel).resolve()
    if not target.is_relative_to(root):
        raise AppError("This file is outside the workspace folder.")
    return target


def ollama_json(endpoint: str, payload: dict | None = None, timeout=180) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(OLLAMA + endpoint, data=data, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read(MAX_INPUT * 2))
    except error.HTTPError as exc:
        try:
            message = json.loads(exc.read().decode("utf-8")).get("error", str(exc))
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = str(exc)
        raise AppError(f"Ollama error: {message}. Try running setup_smart.cmd.") from exc
    except (error.URLError, TimeoutError, ConnectionError) as exc:
        raise AppError("Can't connect to Ollama on this PC. Install/start Ollama, then run setup_smart.cmd.") from exc
    except json.JSONDecodeError as exc:
        raise AppError("Ollama returned an invalid response.") from exc


def available_models() -> list[str]:
    result = ollama_json("/api/tags", timeout=3)
    return [m["name"] for m in result.get("models", []) if isinstance(m.get("name"), str)]


def validate_model(model: object) -> str:
    if not isinstance(model, str) or not (0 < len(model) <= 90) or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-/" for ch in model):
        raise AppError("Invalid model selection.")
    return model


def chat(model: str, history: list[dict], *, file_mode=False) -> str:
    if not isinstance(history, list) or not history:
        raise AppError("Type a message first.")
    safe_messages = []
    for item in history[-16:]:
        if not isinstance(item, dict):
            continue
        role, content = item.get("role"), item.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and 0 < len(content) <= 30000:
            safe_messages.append({"role": role, "content": content})
    if not safe_messages or safe_messages[-1]["role"] != "user":
        raise AppError("Type a user message first.")
    prompt = SYSTEM_PROMPT
    if file_mode:
        prompt += "\nYou are generating the FULL CONTENTS of ONE code file. Return only the file contents, with no Markdown fences or extra commentary."
    data = ollama_json("/api/chat", {"model": model, "stream": False,
        "messages": [{"role": "system", "content": prompt}] + safe_messages,
        "options": {"temperature": 0.25 if file_mode else 0.55, "num_predict": 2500}}, timeout=240)
    content = data.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise AppError("The model didn't return an answer. Try again.")
    return content.strip()


def strip_code_fences(value: str) -> str:
    """Remove just one full-document Markdown code fence, if model adds it."""
    s = value.strip()
    if not s.startswith("```"):
        return s + "\n"
    lines = s.splitlines()
    if len(lines) > 2 and lines[-1].strip() == "```" and lines[0].startswith("```"):
        return "\n".join(lines[1:-1]).rstrip() + "\n"
    return s + "\n"


class Handler(BaseHTTPRequestHandler):
    server_version = "MyFirstAISmart/1.0"

    def send_json(self, data: dict, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _host_ok(self) -> bool:
        host = self.headers.get("Host", "")
        return host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        if not self._host_ok():
            self.send_json({"error": "Local requests only."}, 403)
            return
        path = urlsplit(self.path).path
        if path in ("/", "/index.html"):
            body = WEBPAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/status":
            try:
                models = available_models()
                self.send_json({"online": True, "models": models, "default_model": DEFAULT_MODEL})
            except AppError as exc:
                self.send_json({"online": False, "models": [], "error": str(exc), "default_model": DEFAULT_MODEL})
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_json({"error": "Not found."}, 404)

    def do_POST(self):
        if not self._host_ok():
            self.send_json({"error": "Local requests only."}, 403)
            return
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
            self.send_json({"error": "Request blocked."}, 403)
            return
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            self.send_json({"error": "JSON is required."}, 415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_INPUT:
                raise AppError("Request is too big or empty.")
            obj = json.loads(self.rfile.read(length))
            if not isinstance(obj, dict):
                raise AppError("Expected an object.")
            path = urlsplit(self.path).path
            if path == "/api/chat":
                reply = chat(validate_model(obj.get("model", DEFAULT_MODEL)), obj.get("messages", []))
                self.send_json({"reply": reply})
            elif path == "/api/generate-file":
                target = workspace_path(obj.get("filename"))
                description = obj.get("description")
                if not isinstance(description, str) or not (3 <= len(description) <= 10000):
                    raise AppError("Please describe what to build (3–10000 characters).")
                old = ""
                if target.exists():
                    if target.stat().st_size > MAX_FILE:
                        raise AppError("That file is too big to edit with this tool.")
                    old = target.read_text(encoding="utf-8")
                prompt = (f"Create or edit the file named '{target.relative_to(WORKSPACE.resolve()).as_posix()}'.\n"
                          f"Request: {description}\n"
                          f"Current contents of that file (empty means new):\n<<<EXISTING_FILE>>>\n{old[:50000]}\n<<<END_EXISTING_FILE>>>\n"
                          "Return the COMPLETE updated file content. Do not omit unchanged portions.")
                generated = chat(validate_model(obj.get("model", DEFAULT_MODEL)), [{"role": "user", "content": prompt}], file_mode=True)
                self.send_json({"filename": target.relative_to(WORKSPACE.resolve()).as_posix(),
                                "content": strip_code_fences(generated), "existing": target.exists()})
            elif path == "/api/save-file":
                target = workspace_path(obj.get("filename"))
                contents = obj.get("content")
                if not isinstance(contents, str) or len(contents.encode("utf-8")) > MAX_FILE:
                    raise AppError("Code is too large to save (256 KB limit).")
                target.parent.mkdir(parents=True, exist_ok=True)
                # Resolve again after creating parent to reject folders linking outside workspace.
                target = workspace_path(obj.get("filename"))
                target.write_text(contents, encoding="utf-8")
                self.send_json({"saved": True, "filename": target.relative_to(WORKSPACE.resolve()).as_posix()})
            else:
                self.send_json({"error": "Not found."}, 404)
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError, AppError, OSError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except Exception:
            self.send_json({"error": "Unexpected server error. See the terminal."}, 500)
            raise


def main():
    WORKSPACE.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, 8765), Handler)
    url = f"http://{HOST}:{server.server_port}/"
    print("=" * 55)
    print(" MyFirstAI SMART — Your local AI coding assistant")
    print("=" * 55)
    print("Runs locally. Code files are only saved after approval.")
    print("Open:", url)
    print("Use setup_smart.cmd first to install the AI model.")
    print("Press Ctrl+C to stop.\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nClosing MyFirstAI Smart.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
