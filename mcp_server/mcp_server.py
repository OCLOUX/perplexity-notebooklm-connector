#!/usr/bin/env python3
"""
Serveur MCP HTTP pour NotebookLM - Compatible Perplexity Desktop v4
Spec MCP 2024-11-05 / JSON-RPC 2.0 strict
- GET /mcp : JSON si sondage, SSE si Accept: text/event-stream
- Routes OAuth discovery incluses
"""
import json
import os
import re
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

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
        "description": "Cree un notebook NotebookLM et y injecte un texte (reponse Perplexity).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titre du notebook"},
                "text": {"type": "string", "description": "Contenu texte a injecter comme source"},
                "source_title": {"type": "string", "description": "Titre de la source"},
                "urls": {"type": "array", "items": {"type": "string"}, "description": "URLs supplementaires"},
            },
            "required": ["title", "text"],
        },
    },
    {
        "name": "add_source_to_notebook",
        "description": "Ajoute une source texte ou URL a un notebook existant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "ID du notebook"},
                "text": {"type": "string", "description": "Texte a ajouter"},
                "url": {"type": "string", "description": "URL a ajouter"},
                "source_title": {"type": "string", "description": "Titre de la source"},
            },
            "required": ["notebook_id"],
        },
    },
]

WELL_KNOWN_OAUTH = {
    "resource": "",
    "authorization_servers": [],
    "scopes_supported": [],
    "bearer_methods_supported": ["header"],
}

SERVER_INFO = {
    "name": "notebooklm-mcp",
    "version": "4.0.0",
    "description": "Serveur MCP NotebookLM pour Perplexity Desktop",
    "tools": [t["name"] for t in TOOLS],
}


def run_nlm(args):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        ["nlm"] + args,
        capture_output=True, text=True, shell=False,
        encoding="utf-8", errors="replace", env=env,
    )
    return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "returncode": r.returncode}


def parse_notebook_id(output):
    for pat in [
        r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
        r"notebook(?:_id)?[\s:=]+([A-Za-z0-9_-]+)",
    ]:
        m = re.search(pat, output, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def call_tool(name, arguments):
    if name == "list_notebooks":
        result = run_nlm(["notebook", "list", "--json"])
        if result["returncode"] != 0:
            return {"error": result["stderr"] or result["stdout"]}
        try:
            return json.loads(result["stdout"])
        except Exception:
            return {"raw": result["stdout"]}
    elif name == "create_notebook":
        title = arguments.get("title", "Notebook Perplexity")
        text = arguments.get("text", "")
        source_title = arguments.get("source_title", "Perplexity import")
        urls = arguments.get("urls", [])
        r = run_nlm(["notebook", "create", title])
        out = r["stdout"] + "\n" + r["stderr"]
        notebook_id = parse_notebook_id(out)
        if not notebook_id:
            return {"error": f"Impossible d'extraire l'ID. Sortie: {out}"}
        run_nlm(["source", "add", notebook_id, "--text", text, "--title", source_title])
        for url in urls:
            run_nlm(["source", "add", notebook_id, "--url", url])
        return {
            "ok": True,
            "notebook_id": notebook_id,
            "notebook_url": f"https://notebooklm.google.com/notebook/{notebook_id}",
        }
    elif name == "add_source_to_notebook":
        notebook_id = arguments.get("notebook_id")
        source_title = arguments.get("source_title", "Source import")
        if "text" in arguments:
            r = run_nlm(["source", "add", notebook_id, "--text", arguments["text"], "--title", source_title])
        elif "url" in arguments:
            r = run_nlm(["source", "add", notebook_id, "--url", arguments["url"]])
        else:
            return {"error": "Fournissez text ou url."}
        return {"ok": r["returncode"] == 0, "stdout": r["stdout"], "stderr": r["stderr"]}
    return {"error": f"Outil inconnu: {name}"}


def json_resp(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept, Mcp-Session-Id")
    handler.end_headers()
    handler.wfile.write(body)


def sse_resp(handler):
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "keep-alive")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    msg = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    handler.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
    handler.wfile.flush()


class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[MCP] {self.address_string()} {fmt % args}", flush=True)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept, Mcp-Session-Id")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]  # ignorer query string
        accept = self.headers.get("Accept", "")
        print(f"[MCP] GET {path} Accept={accept}", flush=True)

        # Routes OAuth discovery
        if path in (
            "/.well-known/oauth-protected-resource",
            "/mcp/.well-known/oauth-protected-resource",
            "/.well-known/oauth-authorization-server",
            "/mcp/.well-known/oauth-authorization-server",
        ):
            json_resp(self, WELL_KNOWN_OAUTH)
            return

        # Endpoint MCP principal
        if path in ("/mcp", "/mcp/sse", "/sse", "/"):
            # Si le client demande explicitement SSE -> streaming
            if "text/event-stream" in accept:
                sse_resp(self)
            else:
                # Sinon sondage de validation -> JSON
                json_resp(self, SERVER_INFO)
            return

        if path == "/health":
            json_resp(self, {"ok": True, "server": "notebooklm-mcp", "version": "4.0.0"})
            return

        print(f"[MCP] GET 404: {path}", flush=True)
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        print(f"[MCP] POST {self.path}: {body[:300]}", flush=True)
        try:
            msg = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        method = msg.get("method", "")
        req_id = msg.get("id")
        params = msg.get("params") or {}

        # Notifications -> HTTP 202 sans body
        if req_id is None or method.startswith("notifications/"):
            print(f"[MCP] Notification: {method}", flush=True)
            self.send_response(202)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "notebooklm-mcp", "version": "4.0.0"},
                    "instructions": "Outils disponibles: list_notebooks, create_notebook, add_source_to_notebook.",
                },
            }
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments") or {}
            result = call_tool(tool_name, arguments)
            resp = {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                    "isError": "error" in result,
                },
            }
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
        else:
            resp = {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        json_resp(self, resp)


if __name__ == "__main__":
    print(f"Serveur MCP NotebookLM v4 sur http://{HOST}:{PORT}/mcp", flush=True)
    print("Outils : list_notebooks, create_notebook, add_source_to_notebook", flush=True)
    print("Ctrl+C pour arreter.", flush=True)
    HTTPServer((HOST, PORT), MCPHandler).serve_forever()
