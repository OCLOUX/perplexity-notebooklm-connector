# Serveur MCP HTTP NotebookLM

Serveur MCP HTTP minimal en Python pur, compatible **Perplexity Desktop** (mode HTTP diffusable en continu / SSE).

## Prérequis

- Python 3.8+
- `nlm` installé et authentifié
- [ngrok](https://ngrok.com/download) pour exposer le serveur publiquement

## Outils MCP exposés

| Outil | Description |
|-------|-------------|
| `list_notebooks` | Liste tous les notebooks NotebookLM |
| `create_notebook` | Crée un notebook et y injecte un texte Perplexity |
| `add_source_to_notebook` | Ajoute une source texte ou URL à un notebook existant |

## Démarrage

### Option A : local

```powershell
.\start_mcp_server.ps1
```

### Option B : avec ngrok (pour Perplexity Desktop)

```powershell
.\start_with_ngrok.ps1
```

Ngrok affiche une URL publique du type `https://abc123.ngrok-free.app`.

## Configuration Perplexity Desktop

1. **Settings → Connectors → Ajouter un connecteur personnalisé**
2. Remplissez :
   - **Nom** : `NotebookLM`
   - **URL du serveur MCP distant** : `https://abc123.ngrok-free.app/mcp`
   - **Authentification** : `Aucune`
   - **Transports** : `HTTP diffusable en continu`
   - **Accès réseau** : `Public`
3. Cochez la case → **Ajouter**

## Exemples de prompts dans Perplexity

- *"Crée un notebook NotebookLM 'Veille cybersécurité' avec ce résumé comme source"*
- *"Liste mes notebooks NotebookLM"*
- *"Ajoute cette URL à mon notebook ID xxxx"*
