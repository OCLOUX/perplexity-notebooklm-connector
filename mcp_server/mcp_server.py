#!/usr/bin/env python3
"""
Serveur MCP HTTP pour NotebookLM - Compatible Perplexity Desktop v8.1
Spec MCP 2025-06-18 / JSON-RPC 2.0 / HTTP 1.1
- HOST force sur 127.0.0.1 (evite ERR_NGROK_8012 / conflit IPv6)
- DELETE /mcp supporte (fermeture de session)
- Sessions gerees en memoire
- ConnectionAbortedError silencieux
"""
import json
import os
import re
import subprocess
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("MCP_PORT", 3000))
# CRITIQUE : forcer 127.0.0.1 et non 0.0.0.0 pour eviter que ngrok
# tente de se connecter via IPv6 [::1] et echoue avec ERR_NGROK_8012
HOST = os.environ.get("MCP_HOST", "127.0.0.1")
PROTOCOL_VERSION = "2025-06-18"

SESSIONS = {}

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
    "version": "8.1.0",
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


def send_json(handler, data, status=200, extra_headers=None):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    try:
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Connection", "keep-alive")
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept, Mcp-Session-Id")
        handler.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id")
        if extra_headers:
            for k, v in extra_headers.items():
                handler.send_header(k, v)
        handler.end_headers()
        handler.wfile.write(body)
        handler.wfile.flush()
    except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
        pass


def send_sse(handler):
    try:
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.send_header("Connection", "keep-alive")
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        msg = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        handler.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
        handler.wfile.flush()
    except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
        pass


class MCPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print(f"[MCP] {self.address_string()} {fmt % args}", flush=True)

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept, Mcp-Session-Id")
            self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id")
            self.send_header("Content-Length", "0")
            self.end_headers()
        except (ConnectionAbortedError, BrokenPipeError):
            pass

    def do_DELETE(self):
        session_id = self.headers.get("Mcp-Session-Id", "")
        if session_id in SESSIONS:
            del SESSIONS[session_id]
        print(f"[MCP] DELETE session={session_id}", flush=True)
        try:
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        except (ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self):
        path = self.path.split("?")[0]
        accept = self.headers.get("Accept", "")
        print(f"[MCP] GET {path} Accept={accept}", flush=True)

        if path in (
            "/.well-known/oauth-protected-resource",
            "/mcp/.well-known/oauth-protected-resource",
            "/.well-known/oauth-authorization-server",
            "/mcp/.well-known/oauth-authorization-server",
        ):
            send_json(self, WELL_KNOWN_OAUTH)
            return

        if path in ("/mcp", "/mcp/sse", "/sse", "/"):
            if "text/event-stream" in accept:
                send_sse(self)
            else:
                send_json(self, SERVER_INFO)
            return

        if path == "/health":
            send_json(self, {"ok": True, "server": "notebooklm-mcp", "version": "8.1.0"})
            return

        try:
            body = b"Not Found"
            self.send_response(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError):
            pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        print(f"[MCP] POST {self.path}: {raw[:400]}", flush=True)
        try:
            msg = json.loads(raw)
        except Exception:
            try:
                err = b"Bad Request"
                self.send_response(400)
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)
            except (ConnectionAbortedError, BrokenPipeError):
                pass
            return

        method = msg.get("method", "")
        req_id = msg.get("id")  # 0 = valide, None = notification
        params = msg.get("params") or {}

        is_notification = (req_id is None) or method.startswith("notifications/")
        if is_notification:
            print(f"[MCP] Notification: {method}", flush=True)
            try:
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
            except (ConnectionAbortedError, BrokenPipeError):
                pass
            return

        client_protocol = params.get("protocolVersion", PROTOCOL_VERSION)

        if method == "initialize":
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = True
            resp = {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": client_protocol,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "logging": {},
                    },
                    "serverInfo": {"name": "notebooklm-mcp", "version": "8.1.0"},
                    "instructions": "Outils: list_notebooks, create_notebook, add_source_to_notebook.",
                },
            }
            send_json(self, resp, extra_headers={"Mcp-Session-Id": session_id})
            return

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

        send_json(self, resp)


if __name__ == "__main__":
    print(f"Serveur MCP NotebookLM v8.1 sur http://{HOST}:{PORT}/mcp", flush=True)
    print(f"Protocole : {PROTOCOL_VERSION} / HTTP/1.1", flush=True)
    print("Outils : list_notebooks, create_notebook, add_source_to_notebook", flush=True)
    print("Ctrl+C pour arreter.", flush=True)
    HTTPServer((HOST, PORT), MCPHandler).serve_forever()
