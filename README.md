# Perplexity -> NotebookLM Connector

Connecteur MCP qui permet a **Perplexity Desktop** de creer et alimenter des notebooks **Google NotebookLM** automatiquement.

> Teste et fonctionnel sur Windows 10/11 avec Python 3.14, ngrok v3, Perplexity Desktop.

---

## Table des matieres

1. [Ce que ca fait](#ce-que-ca-fait)
2. [Comptes et APIs necessaires](#comptes-et-apis-necessaires)
3. [Prerequis logiciels](#prerequis-logiciels)
4. [Installation complete](#installation-complete)
5. [Tests de connexion](#tests-de-connexion)
6. [Demarrage quotidien](#demarrage-quotidien)
7. [Configuration Perplexity Desktop](#configuration-perplexity-desktop)
8. [Depannage](#depannage)
9. [Architecture](#architecture)

---

## Ce que ca fait

```
Perplexity Desktop  ->  ngrok (tunnel HTTPS)  ->  mcp_server.py  ->  NotebookLM
```

1. Vous posez une question dans Perplexity Desktop
2. Perplexity appelle le serveur MCP via ngrok
3. Le serveur cree un notebook dans NotebookLM avec la reponse comme source
4. Vous retrouvez vos recherches organisees dans NotebookLM

---

## Comptes et APIs necessaires

Avant de commencer, vous avez besoin de **3 comptes** et leurs cles/tokens. Tout est gratuit.

### 1. Compte Google (pour NotebookLM)

- **Pourquoi** : NotebookLM est un service Google. Le CLI `nlm` utilise votre compte Google pour creer et modifier des notebooks.
- **Creer** : https://accounts.google.com/signup (gratuit)
- **NotebookLM** : https://notebooklm.google.com (gratuit, connectez-vous avec votre compte Google)
- **Aucune cle API a generer** : l'authentification se fait via le navigateur (`nlm auth login`).

> Limite gratuite : jusqu'a 100 notebooks, 50 sources par notebook.

---

### 2. Compte ngrok (pour le tunnel HTTPS)

- **Pourquoi** : Perplexity Desktop ne peut appeler que des URLs HTTPS publiques. ngrok cree un tunnel securise entre Internet et votre ordinateur.
- **Creer** : https://ngrok.com (gratuit)
- **Obtenir l'Authtoken** :
  1. Connectez-vous sur https://dashboard.ngrok.com
  2. Allez dans **"Your Authtoken"** : https://dashboard.ngrok.com/get-started/your-authtoken
  3. Copiez le token (commence par `2...`)
  4. Collez-le dans votre terminal :
     ```powershell
     ngrok config add-authtoken VOTRE_TOKEN_ICI
     ```

> Plan gratuit : 1 tunnel actif, URL aleatoire qui change a chaque redemarrage.
> Plan payant : URL fixe (domaine personnalise).

**Ou trouver le token :**
```
https://dashboard.ngrok.com/get-started/your-authtoken
                             ^
                             Cliquez ici apres connexion
```

---

### 3. Perplexity Desktop avec MCP

- **Pourquoi** : Perplexity Desktop (version bureau) supporte le protocole MCP pour appeler des outils externes.
- **Telecharger** : https://www.perplexity.ai/desktop
- **Aucun token API necessaire** pour le MCP local : il suffit d'ajouter l'URL du serveur dans les parametres.
- **Note** : la version web de Perplexity ne supporte pas MCP. Il faut obligatoirement l'application bureau.

---

### Recap des comptes

| Service | Compte | Token/Cle | Ou le trouver |
|---------|--------|-----------|---------------|
| Google NotebookLM | Compte Google | Aucun (auth navigateur) | https://accounts.google.com |
| ngrok | Compte ngrok | Authtoken | https://dashboard.ngrok.com/get-started/your-authtoken |
| Perplexity Desktop | Compte Perplexity | Aucun (config URL) | https://www.perplexity.ai/desktop |

---

## Prerequis logiciels

### 1. Python 3.9+

Telecharger : https://www.python.org/downloads/

> IMPORTANT : cochez **"Add Python to PATH"** lors de l'installation.

Verification :
```powershell
python --version
# Doit afficher : Python 3.x.x
```

### 2. ngrok

Telecharger : https://ngrok.com/download (choisir Windows)

1. Extraire `ngrok.exe` dans un dossier de votre choix (ex: `C:\ngrok\`)
2. Ajouter ce dossier au PATH Windows, ou placer `ngrok.exe` dans `C:\Windows\System32\`
3. Configurer votre token :
```powershell
ngrok config add-authtoken VOTRE_TOKEN_ICI
```

Verification :
```powershell
ngrok version
# Doit afficher : ngrok version 3.x.x
```

### 3. nlm (NotebookLM CLI)

```powershell
pip install notebooklm-cli
```

Connexion a votre compte Google :
```powershell
nlm auth login
# Un navigateur s'ouvre -> connectez-vous avec votre compte Google
```

Verification :
```powershell
nlm notebook list
# Doit lister vos notebooks NotebookLM existants
```

### 4. Perplexity Desktop

Telecharger : https://www.perplexity.ai/desktop

---

## Installation complete

### Option A - Script automatique (recommande)

```powershell
# 1. Cloner le repo
git clone https://github.com/OCLOUX/perplexity-notebooklm-connector.git
cd perplexity-notebooklm-connector

# 2. Lancer le script d'installation
powershell -ExecutionPolicy Bypass -File OCLOUX-NotebookLMConnector.ps1
```

Le script verifie automatiquement Python, ngrok et nlm, puis lance les tests.

### Option B - Installation manuelle

```powershell
# 1. Cloner le repo
git clone https://github.com/OCLOUX/perplexity-notebooklm-connector.git
cd perplexity-notebooklm-connector

# 2. Verifier que tout est installe
python --version
ngrok version
nlm --version

# 3. Verifier la connexion NotebookLM
nlm notebook list

# 4. Lancer les tests de connexion
powershell -ExecutionPolicy Bypass -File test_connection.ps1
```

---

## Tests de connexion

Avant de configurer Perplexity, verifiez que tout fonctionne :

```powershell
powershell -ExecutionPolicy Bypass -File test_connection.ps1
```

Ce script verifie dans l'ordre :
- Python disponible
- ngrok disponible
- nlm disponible et authentifie
- Serveur MCP demarre sur le port 3000
- Endpoint `/health` repond correctement
- Endpoint `/mcp` repond au protocole JSON-RPC

Sortie attendue :
```
[1/6] Python.............. OK (3.14.x)
[2/6] ngrok............... OK (3.39.x)
[3/6] nlm................. OK
[4/6] NotebookLM auth..... OK (X notebooks trouves)
[5/6] Serveur MCP......... OK (http://127.0.0.1:3000/health)
[6/6] Protocole MCP....... OK (initialize -> 200)
Tous les tests passent ! Vous pouvez lancer OCLOUX-NotebookLMConnector-start.ps1
```

---

## Demarrage quotidien

Une seule commande pour tout demarrer :

```powershell
powershell -ExecutionPolicy Bypass -File OCLOUX-NotebookLMConnector-start.ps1
```

Ce script :
1. Demarre `mcp_server.py` dans une fenetre PowerShell
2. Demarre `ngrok http 127.0.0.1:3000` dans une autre fenetre
3. Affiche l'URL ngrok a copier dans Perplexity Desktop
4. Copie automatiquement l'URL dans le presse-papiers

> A relancer a chaque demarrage de Windows (l'URL ngrok change a chaque fois sur le plan gratuit).

---

## Configuration Perplexity Desktop

1. Ouvrez Perplexity Desktop
2. Allez dans **Settings -> MCP Servers** (ou **Parametres -> Serveurs MCP**)
3. Cliquez **Add Server** / **Ajouter un serveur**
4. Remplissez :
   - **Name** : `NotebookLM`
   - **URL** : `https://VOTRE-URL.ngrok-free.app/mcp`
     (remplacez par l'URL affichee par `OCLOUX-NotebookLMConnector-start.ps1`)
5. Cliquez **Save** / **Enregistrer**
6. Perplexity detecte automatiquement les 3 outils :
   - `list_notebooks` - lister vos notebooks
   - `create_notebook` - creer un notebook avec du texte
   - `add_source_to_notebook` - ajouter une source a un notebook existant

> L'URL ngrok change a chaque redemarrage (plan gratuit). Pensez a la mettre a jour dans Perplexity.

---

## Depannage

### ERR_NGROK_8012 (502 Bad Gateway)

ngrok ne trouve pas le serveur. Verifiez que `mcp_server.py` est bien demarre :
```powershell
curl http://127.0.0.1:3000/health
# Doit repondre : {"ok": true, "server": "notebooklm-mcp", "version": "8.2.0"}
```

Si pas de reponse -> relancer le serveur :
```powershell
cd mcp_server
python mcp_server.py
```

> ngrok doit etre lance avec `ngrok http 127.0.0.1:3000` (IPv4 explicite), pas `ngrok http 3000` qui peut utiliser IPv6 `[::1]` sur Windows et echouer.

### curl ne repond pas mais le navigateur oui

Windows curl utilise IPv6 par defaut. Utilisez toujours :
```powershell
curl http://127.0.0.1:3000/health   # OK - IPv4 explicite
# et NON :
curl http://localhost:3000/health   # peut aller sur [::1]
```

### nlm : erreur d'authentification

```powershell
nlm auth login
# Reconnectez-vous avec votre compte Google
```

### Port 3000 deja utilise

```powershell
netstat -ano | findstr :3000
# Notez le PID, puis :
taskkill /PID <PID> /F
```

### ConnectionAbortedError dans les logs Python

C'est **normal** - Perplexity / ngrok ferme parfois la connexion apres avoir recu la reponse. Le serveur l'ignore silencieusement depuis la v8.2.

---

## Architecture

```
perplexity-notebooklm-connector/
|-- README.md                              <- Ce fichier
|-- OCLOUX-NotebookLMConnector.ps1         <- Script d'installation automatique
|-- OCLOUX-NotebookLMConnector-start.ps1   <- Demarrage tout-en-un (serveur + ngrok)
|-- test_connection.ps1                    <- Tests de connexion complets (6 etapes)
`-- mcp_server/
    |-- mcp_server.py                      <- Serveur MCP HTTP (v8.2)
    |-- start_mcp_server.ps1              <- Demarrer le serveur seul
    `-- start_with_ngrok.ps1              <- Demarrer serveur + ngrok
```

### Flux technique detaille

```
[Perplexity Desktop]
    |
    |  HTTPS POST /mcp  (JSON-RPC 2.0, spec MCP 2025-06-18)
    v
[ngrok tunnel]  (https://xxx.ngrok-free.app)
    |  forward vers
    v
[mcp_server.py :3000]  <- ThreadingHTTPServer Python sur 127.0.0.1
    |  appelle
    v
[nlm CLI]              <- notebooklm-cli (pip)
    |  API Google OAuth
    v
[Google NotebookLM]    <- https://notebooklm.google.com
```

### Outils MCP exposes

| Outil | Description | Parametres |
|-------|-------------|------------|
| `list_notebooks` | Liste tous vos notebooks | aucun |
| `create_notebook` | Cree un notebook avec du texte | `title`, `text`, `source_title`, `urls` |
| `add_source_to_notebook` | Ajoute une source a un notebook existant | `notebook_id`, `text` ou `url`, `source_title` |

---

## Versions

| Version | Changements |
|---------|-------------|
| v8.2 | ThreadingHTTPServer - resout les 502 ngrok sur requetes simultanees |
| v8.1 | HOST force sur 127.0.0.1 - resout ERR_NGROK_8012 (IPv6) |
| v8 | do_DELETE ajoute - resout 501 sur fermeture de session MCP |
| v7 | Mcp-Session-Id - spec MCP 2025-06-18 |

---

*Projet maintenu par [OCLOUX](https://github.com/OCLOUX)*
