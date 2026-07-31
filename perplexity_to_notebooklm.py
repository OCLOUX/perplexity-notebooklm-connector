#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, capture=True, check=True):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        shell=False,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if check and r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or f"Command failed: {' '.join(cmd)}").strip())
    return r


def require_nlm():
    try:
        run_cmd(["nlm", "--help"])
    except Exception as e:
        raise SystemExit(
            "Le binaire nlm est introuvable. Installez notebooklm-mcp-cli puis éxécutez nlm login.\n"
            f"Détail: {e}"
        )


def parse_notebook_id(output):
    patterns = [
        r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
        r"notebook(?:_id)?[\s:=]+([A-Za-z0-9_-]+)",
        r"\bid[\s:=]+([A-Za-z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, output, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def create_notebook(title):
    result = run_cmd(["nlm", "notebook", "create", title])
    out = (result.stdout or "") + "\n" + (result.stderr or "")
    notebook_id = parse_notebook_id(out)
    if not notebook_id:
        raise RuntimeError("Impossible d'extraire l'identifiant du notebook depuis la sortie de nlm.\n" + out)
    return notebook_id, out.strip()


def add_text_source(notebook_id, text, source_title=None, wait=False):
    cmd = ["nlm", "source", "add", notebook_id, "--text", text]
    if source_title:
        cmd += ["--title", source_title]
    if wait:
        cmd += ["--wait"]
    return run_cmd(cmd, capture=True, check=True)


def add_url_source(notebook_id, url, wait=False):
    cmd = ["nlm", "source", "add", notebook_id, "--url", url]
    if wait:
        cmd += ["--wait"]
    return run_cmd(cmd, capture=True, check=True)


def load_text(args):
    if args.text:
        return args.text
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Aucun contenu fourni. Utilisez --text, --text-file ou pipez le texte via STDIN.")


def main():
    p = argparse.ArgumentParser(description="Crée un notebook NotebookLM et y ajoute le contenu d'une réponse Perplexity.")
    p.add_argument("--title", required=True, help="Titre du notebook à créer")
    p.add_argument("--source-title", default="Perplexity import", help="Titre de la source texte")
    p.add_argument("--text", help="Texte Perplexity à injecter")
    p.add_argument("--text-file", help="Fichier texte/markdown à injecter")
    p.add_argument("--url", action="append", default=[], help="URL source à ajouter en plus du texte")
    p.add_argument("--wait", action="store_true", help="Attend la fin de l'indexation")
    p.add_argument("--open", action="store_true", dest="open_browser", help="Ouvre le notebook dans le navigateur")
    p.add_argument("--json", action="store_true", help="Retourne un résultat JSON")
    args = p.parse_args()

    require_nlm()
    text = load_text(args)
    notebook_id, create_output = create_notebook(args.title)
    text_result = add_text_source(notebook_id, text, args.source_title, wait=args.wait)

    url_results = []
    for url in args.url:
        r = add_url_source(notebook_id, url, wait=args.wait)
        url_results.append({"url": url, "stdout": (r.stdout or "").strip(), "stderr": (r.stderr or "").strip()})

    notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"
    if args.open_browser:
        import webbrowser
        webbrowser.open(notebook_url)

    payload = {
        "ok": True,
        "notebook_id": notebook_id,
        "notebook_url": notebook_url,
        "create_output": create_output,
        "text_source_stdout": (text_result.stdout or "").strip(),
        "text_source_stderr": (text_result.stderr or "").strip(),
        "urls_added": url_results,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Notebook créé : {notebook_id}")
        print(f"URL : {notebook_url}")
        if args.url:
            print(f"URLs ajoutées : {len(args.url)}")


if __name__ == "__main__":
    main()
