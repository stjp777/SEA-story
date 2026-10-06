"""Storyboard generator: stdlib web server + local Ollama. Run: python app.py, open http://localhost:8000"""
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODEL = "llama3.2:3b"  # swap for "llama3.2:1b" on slow machines
OLLAMA_URL = "http://localhost:11434/api/chat"
HERE = Path(__file__).parent
FIELDS = ["main_character", "reveal", "supporting_1", "supporting_2", "plot", "theme"]

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"title": {"type": "string"}, "description": {"type": "string"}},
                "required": ["title", "description"],
            },
        },
        "ending": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "reveal": {"type": "string"},
                "cliffhanger": {"type": "string"},
            },
            "required": ["description", "reveal", "cliffhanger"],
        },
    },
    "required": ["title", "scenes", "ending"],
}


def build_prompt(s):
    return (
        "Write a storyboard as JSON.\n"
        f"Main character: {s['main_character']}\n"
        f"Supporting characters: {s['supporting_1']} and {s['supporting_2']}\n"
        f"Plot: {s['plot']}\n"
        f"Theme: {s['theme']}\n"
        "Give 4 to 6 scenes, each a short title and a 2-3 sentence visual description "
        "that uses the characters by name and reflects the theme.\n"
        f"Then an ending scene. In 'reveal', state plainly that {s['main_character']} {s['reveal']}. "
        "In 'cliffhanger', end on an unresolved moment that sets up the next scene."
    )


def validate(board):
    """Return error string, or None if the board is usable."""
    if not isinstance(board, dict):
        return "not an object"
    scenes = board.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return "no scenes"
    if not all(isinstance(x, dict) and x.get("title") and x.get("description") for x in scenes):
        return "scene missing title/description"
    end = board.get("ending")
    if not isinstance(end, dict) or not all(str(end.get(k, "")).strip() for k in ("description", "reveal", "cliffhanger")):
        return "ending missing description/reveal/cliffhanger"
    return None


def generate(story, tries=2):
    body = json.dumps({
        "model": MODEL,
        "stream": False,
        "format": SCHEMA,
        "messages": [{"role": "user", "content": build_prompt(story)}],
    }).encode()
    err = "unknown"
    for _ in range(tries):
        req = urllib.request.Request(OLLAMA_URL, body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            content = json.load(r)["message"]["content"]
        try:
            board = json.loads(content)
        except json.JSONDecodeError:
            err = "model returned invalid JSON"
            continue
        err = validate(board)
        if not err:
            return board
    raise ValueError(f"model output unusable after {tries} tries: {err}")


class Handler(BaseHTTPRequestHandler):
    def send(self, code, data, ctype="application/json"):
        if not isinstance(data, bytes):
            data = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        files = {"/": ("index.html", "text/html; charset=utf-8"), "/data.json": ("data.json", "application/json")}
        if self.path not in files:
            return self.send(404, {"error": "not found"})
        name, ctype = files[self.path]
        self.send(200, (HERE / name).read_bytes(), ctype)

    def do_POST(self):
        if self.path != "/storyboard":
            return self.send(404, {"error": "not found"})
        try:
            raw = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            story = {k: str(raw.get(k, "")).strip()[:300] for k in FIELDS}
        except (ValueError, AttributeError):
            return self.send(400, {"error": "bad JSON"})
        missing = [k for k in FIELDS if not story[k]]
        if missing:
            return self.send(400, {"error": f"missing: {', '.join(missing)}"})
        try:
            self.send(200, generate(story))
        except urllib.error.HTTPError as e:  # e.g. model not pulled
            self.send(502, {"error": f"Ollama error {e.code}: {e.read().decode(errors='replace')}"})
        except urllib.error.URLError as e:
            self.send(502, {"error": f"Ollama not reachable at {OLLAMA_URL} ({e.reason}). Is 'ollama serve' running?"})
        except (ValueError, TimeoutError) as e:
            self.send(502, {"error": str(e)})


if __name__ == "__main__":
    print("Storyboard app on http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
