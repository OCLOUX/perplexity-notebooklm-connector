#!/usr/bin/env python3
"""
Serveur MCP HTTP pour NotebookLM
- Expose les outils MCP via HTTP Streaming (SSE)
- Compatible Perplexity Desktop "HTTP diffusable en continu"
- S'appuie sur le CLI nlm (notebooklm-mcp-cli)
"""
import json
import os
import re
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

PORT = int(os.environ.get("MCP_PORT", 3000))
HOST = os.environ.get("MCP_HOST", "0.0.0.0")

TOOLS = [
    {
        "name": "list_notebooks",
        "description": "Liste tous les notebooks NotebookLM disponibles.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_notebook",
        "description": "Crée un notebook NotebookLM et y injecte un texte (réponse Perplexity).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titre du notebook"},
                "text": {"type": "string", "description": "Contenu texte à injecter comme source"},
                "source_title": {"type": "string", "description": "Titre de la source (défaut: Perplexity import)"},
                "urls": {"type": "array", "items": {"type": "string"}, "description": "URLs supplémentaires à ajouter"},
            },
            "required": ["title", "text"],
        },
    },
    {
        "name": "add_source_to_notebook",
        "description": "Ajoute une source texte ou URL à un notebook existant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "ID du notebook"},
                "text": {"type": "string", "description": "Texte à ajouter"},
                "url": {"type": "string", "description": "URL à ajouter"},
                "source_title": {"type": "string", "description": "Titre de la source"},
            },
            "required": ["notebook_id"],
        },
    },
]


def run_nlm(args: list) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        ["nlm"] + args,
        capture_output=True, text=True, shell=False,
        encoding="utf-8", errors="replace", env=env,
    )
    return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "returncode": r.returncode}


def parse_notebook_id(output: str):
    for pat in [
        r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
        r"notebook(?:_id)?[\s:=]+([A-Za-z0-9_-]+)",
    ]:
        m = re.search(pat, output, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def call_tool(name: str, arguments: dict) -> Any:
    if name == "list_notebooks":
        result = run_nlm(["notebook", "list", "--json"])
        if result["returncode"] != 0:
            return {"error": result["stderr"] or result["stdout"]}
        try:
            return json.loads(result["stdout"])
        except Exception:
            return {"raw": result["stdout"]}

    elif name == "create_notebook":
        title = arguments["title"]
        text = arguments["text"]
        source_title = arguments.get("source_title", "Perplexity import")
        urls = arguments.get("urls", [])
        r = run_nlm(["notebook", "create", title])
        out = r["stdout"] + "\n" + r["stderr"]
        notebook_id = parse_notebook_id(out)
        if not notebook_id:
            return {"error": f"Impossible d'extraire l'ID du notebook. Sortie: {out}"}
        run_nlm(["source", "add", notebook_id, "--text", text, "--title", source_title])
        for url in urls:
            run_nlm(["source", "add", notebook_id, "--url", url])
        return {
            "ok": True,
            "notebook_id": notebook_id,
            "notebook_url": f"https://notebooklm.google.com/notebook/{notebook_id}",
        }

    elif name == "add_source_to_notebook":
        notebook_id = arguments["notebook_id"]
        source_title = arguments.get("source_title", "Source import")
        if "text" in arguments:
            r = run_nlm(["source", "add", notebook_id, "--text", arguments["text"], "--title", source_title])
        elif "url" in arguments:
            r = run_nlm(["source", "add", notebook_id, "--url", arguments["url"]])
        else:
            return {"error": "Fournissez text ou url."}
        return {"ok": r["returncode"] == 0, "stdout": r["stdout"], "stderr": r["stderr"]}

    return {"error": f"Outil inconnu: {name}"}


def make_sse(data: dict) -> bytes:
    return f"data: {json.dumps(data)}\n\n".encode("utf-8")


class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[MCP] {self.address_string()} - {format % args}", flush=True)

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")

    def do_OPTIONS(self):
        self.send_response(200)
        self.cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/mcp", "/mcp/sse", "/sse", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.cors()
            self.end_headers()
            self.wfile.write(make_sse({"jsonrpc": "2.0", "id": 1, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "notebooklm-mcp", "version": "1.0.0"},
            }}))
            self.wfile.flush()
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.cors()
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        method = req.get("method", "")
        req_id = req.get("id")
        params = req.get("params", {})

        if method == "initialize":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "notebooklm-mcp", "version": "1.0.0"},
            }}
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            result = call_tool(params.get("name"), params.get("arguments", {}))
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
            }}
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
        else:
            resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.cors()
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode("utf-8"))


if __name__ == "__main__":
    print(f"Serveur MCP NotebookLM sur http://{HOST}:{PORT}/mcp", flush=True)
    print("Outils : list_notebooks, create_notebook, add_source_to_notebook", flush=True)
    print("Ctrl+C pour arrêter.", flush=True)
    HTTPServer((HOST, PORT), MCPHandler).serve_forever()
