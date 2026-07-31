# 🔗 Perplexity → NotebookLM Connector

Connecteur MCP qui permet à **Perplexity Desktop** de créer et alimenter des notebooks **Google NotebookLM** automatiquement.

> ✅ Testé et fonctionnel sur Windows 10/11 avec Python 3.14, ngrok v3, Perplexity Desktop.

---

## 📋 Table des matières

1. [Ce que ça fait](#ce-que-ça-fait)
2. [Prérequis](#prérequis)
3. [Installation complète](#installation-complète)
4. [Tests de connexion](#tests-de-connexion)
5. [Démarrage quotidien](#démarrage-quotidien)
6. [Configuration Perplexity Desktop](#configuration-perplexity-desktop)
7. [Dépannage](#dépannage)
8. [Architecture](#architecture)

---

## Ce que ça fait

```
Perplexity Desktop  →  ngrok (tunnel HTTPS)  →  mcp_server.py  →  NotebookLM
```

1. Vous posez une question dans Perplexity Desktop
2. Perplexity appelle le serveur MCP via ngrok
3. Le serveur crée un notebook dans NotebookLM avec la réponse comme source
4. Vous retrouvez vos recherches organisées dans NotebookLM

---

## Prérequis

### 1. Python 3.9+

Télécharger : https://www.python.org/downloads/

> ⚠️ **Important** : cochez **"Add Python to PATH"** lors de l'installation.

Vérification :
```powershell
python --version
# Doit afficher : Python 3.x.x
```

### 2. ngrok

Télécharger : https://ngrok.com/download

1. Créez un compte gratuit sur https://ngrok.com
2. Récupérez votre **Authtoken** dans le dashboard : https://dashboard.ngrok.com/get-started/your-authtoken
3. Installez le token :
```powershell
ngrok config add-authtoken VOTRE_TOKEN_ICI
```

Vérification :
```powershell
ngrok version
# Doit afficher : ngrok version 3.x.x
```

### 3. nlm (NotebookLM CLI)

```powershell
pip install notebooklm-cli
```

Connexion à votre compte Google :
```powershell
nlm auth login
# Un navigateur s'ouvre → connectez-vous avec votre compte Google
```

Vérification :
```powershell
nlm notebook list
# Doit lister vos notebooks NotebookLM existants
```

### 4. Perplexity Desktop

Télécharger : https://www.perplexity.ai/desktop

---

## Installation complète

### Option A — Script automatique (recommandé)

```powershell
# 1. Cloner le repo
git clone https://github.com/OCLOUX/perplexity-notebooklm-connector.git
cd perplexity-notebooklm-connector

# 2. Lancer le script d'installation
powershell -ExecutionPolicy Bypass -File install.ps1
```

Le script vérifie automatiquement Python, ngrok et nlm, puis lance les tests.

### Option B — Installation manuelle

```powershell
# 1. Cloner le repo
git clone https://github.com/OCLOUX/perplexity-notebooklm-connector.git
cd perplexity-notebooklm-connector

# 2. Vérifier que tout est installé
python --version
ngrok version
nlm --version

# 3. Vérifier la connexion NotebookLM
nlm notebook list

# 4. Lancer les tests de connexion
powershell -ExecutionPolicy Bypass -File test_connection.ps1
```

---

## Tests de connexion

Avant de configurer Perplexity, vérifiez que tout fonctionne :

```powershell
powershell -ExecutionPolicy Bypass -File test_connection.ps1
```

Ce script vérifie dans l'ordre :
- ✅ Python disponible
- ✅ ngrok disponible
- ✅ nlm disponible et authentifié
- ✅ Serveur MCP démarre sur le port 3000
- ✅ Endpoint `/health` répond correctement
- ✅ Endpoint `/mcp` répond au protocole JSON-RPC

Sortie attendue :
```
[1/6] Python.............. OK (3.14.x)
[2/6] ngrok............... OK (3.39.x)
[3/6] nlm................. OK
[4/6] NotebookLM auth..... OK (X notebooks trouvés)
[5/6] Serveur MCP......... OK (http://127.0.0.1:3000/health)
[6/6] Protocole MCP....... OK (initialize → 200)
✅ Tous les tests passent ! Vous pouvez lancer start_all.ps1
```

---

## Démarrage quotidien

Une seule commande pour tout démarrer :

```powershell
powershell -ExecutionPolicy Bypass -File start_all.ps1
```

Ce script :
1. Démarre `mcp_server.py` dans une fenêtre PowerShell
2. Démarre `ngrok http 127.0.0.1:3000` dans une autre fenêtre
3. Affiche l'URL ngrok à copier dans Perplexity Desktop

> 🔁 À relancer à chaque démarrage de Windows (l'URL ngrok change à chaque fois sur le plan gratuit).

---

## Configuration Perplexity Desktop

1. Ouvrez Perplexity Desktop
2. Allez dans **Settings → MCP Servers** (ou **Paramètres → Serveurs MCP**)
3. Cliquez **Add Server** / **Ajouter un serveur**
4. Remplissez :
   - **Name** : `NotebookLM`
   - **URL** : `https://VOTRE-URL.ngrok-free.app/mcp`
     (remplacez par l'URL affichée par ngrok, ex: `https://autistic-unquote-mortician.ngrok-free.dev/mcp`)
5. Cliquez **Save** / **Enregistrer**
6. Perplexity détecte automatiquement les 3 outils :
   - `list_notebooks` — lister vos notebooks
   - `create_notebook` — créer un notebook avec du texte
   - `add_source_to_notebook` — ajouter une source à un notebook existant

> ⚠️ L'URL ngrok change à chaque redémarrage (plan gratuit). Pensez à la mettre à jour dans Perplexity.

---

## Dépannage

### ERR_NGROK_8012 (502 Bad Gateway)

ngrok ne trouve pas le serveur. Vérifiez que `mcp_server.py` est bien démarré :
```powershell
curl http://127.0.0.1:3000/health
# Doit répondre : {"ok": true, "server": "notebooklm-mcp", "version": "8.2.0"}
```

Si pas de réponse → relancer le serveur :
```powershell
cd mcp_server
python mcp_server.py
```

> ⚠️ ngrok doit être lancé avec `ngrok http 127.0.0.1:3000` (IPv4 explicite), pas `ngrok http 3000` qui peut utiliser IPv6 `[::1]` sur Windows et échouer.

### curl ne répond pas mais le navigateur oui

Windows curl utilise IPv6 par défaut. Utilisez toujours :
```powershell
curl http://127.0.0.1:3000/health   # ✅ IPv4 explicite
# et NON :
curl http://localhost:3000/health   # ❌ peut aller sur [::1]
```

### nlm : erreur d'authentification

```powershell
nlm auth login
# Reconnectez-vous avec votre compte Google
```

### Port 3000 déjà utilisé

```powershell
netstat -ano | findstr :3000
# Notez le PID, puis :
taskkill /PID <PID> /F
```

### ConnectionAbortedError dans les logs Python

C'est **normal** — Perplexity / ngrok ferme parfois la connexion après avoir reçu la réponse. Le serveur l'ignore silencieusement depuis la v8.2.

---

## Architecture

```
perplexity-notebooklm-connector/
├── README.md                  ← Ce fichier
├── install.ps1                ← Script d'installation automatique
├── start_all.ps1              ← Démarrage tout-en-un (serveur + ngrok)
├── test_connection.ps1        ← Tests de connexion complets
└── mcp_server/
    ├── mcp_server.py          ← Serveur MCP HTTP (v8.2)
    ├── start_mcp_server.ps1   ← Démarrer le serveur seul
    └── start_with_ngrok.ps1   ← Démarrer serveur + ngrok
```

### Flux technique détaillé

```
[Perplexity Desktop]
    │
    │  HTTPS POST /mcp  (JSON-RPC 2.0)
    ▼
[ngrok tunnel]
    │  forward vers
    ▼
[mcp_server.py :3000]  ← ThreadingHTTPServer Python
    │  appelle
    ▼
[nlm CLI]              ← notebooklm-cli
    │  API Google
    ▼
[Google NotebookLM]
```

### Outils MCP exposés

| Outil | Description | Paramètres |
|-------|-------------|------------|
| `list_notebooks` | Liste tous vos notebooks | aucun |
| `create_notebook` | Crée un notebook avec du texte | `title`, `text`, `source_title`, `urls` |
| `add_source_to_notebook` | Ajoute une source à un notebook existant | `notebook_id`, `text` ou `url`, `source_title` |

---

## Versions

| Version | Changements |
|---------|-------------|
| v8.2 | ThreadingHTTPServer — résout les 502 ngrok sur requêtes simultanées |
| v8.1 | HOST forcé sur 127.0.0.1 — résout ERR_NGROK_8012 (IPv6) |
| v8 | do_DELETE ajouté — résout 501 sur fermeture de session MCP |
| v7 | Mcp-Session-Id — spec MCP 2025-06-18 |

---

*Projet maintenu par [OCLOUX](https://github.com/OCLOUX)*
