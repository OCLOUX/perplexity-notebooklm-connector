# Connecteur Perplexity → NotebookLM
NE PAS UTILISER : EN COURS DE TEST
Connecteur Python Windows pour créer un notebook **NotebookLM** et y injecter une réponse **Perplexity** via le CLI `nlm`.

## Prérequis

- Python 3.8+
- [`notebooklm-mcp-cli`](https://pypi.org/project/notebooklm-mcp-cli/) installé via `uv tool install notebooklm-mcp-cli`
- Authentification NotebookLM valide : `nlm login`

## Installation

```powershell
.\install_connector.ps1
```

Place les fichiers dans `C:\IA\notebooklm-mcp\perplexity-notebooklm-connector`.

## Utilisation

### Test direct

```powershell
cd C:\IA\notebooklm-mcp\perplexity-notebooklm-connector
python .\perplexity_to_notebooklm.py --title "Test Perplexity" --text "Bonjour" --open
```

### Depuis le presse-papiers (usage réel)

1. Copiez une réponse Perplexity.
2. Lancez :

```powershell
.\run_from_clipboard.ps1 -Title "Veille cybersécurité" -Open
```

### Avec URL supplémentaires

```powershell
python .\perplexity_to_notebooklm.py --title "Recherche" --text-file reponse.md --url "https://example.org" --open
```

### Sortie JSON

```powershell
python .\perplexity_to_notebooklm.py --title "Test" --text "Bonjour" --json
```

## Arguments disponibles

| Argument | Description |
|----------|-------------|
| `--title` | Titre du notebook à créer (obligatoire) |
| `--text` | Texte à injecter comme source |
| `--text-file` | Fichier texte/markdown à injecter |
| `--source-title` | Titre de la source texte (défaut : "Perplexity import") |
| `--url` | URL supplémentaire à ajouter (répétable) |
| `--wait` | Attend la fin de l'indexation des sources |
| `--open` | Ouvre le notebook dans le navigateur |
| `--json` | Retourne le résultat en JSON |

## Fonctionnement

1. Vérifie que `nlm` est disponible et authentifié.
2. Exécute `nlm notebook create <titre>`.
3. Injecte le texte via `nlm source add <id> --text ...`.
4. Ajoute les URLs via `nlm source add <id> --url ...`.
5. Ouvre le notebook dans le navigateur si `--open`.

## Auteur

[OCLOUX](https://github.com/OCLOUX) — Ham Radio / Cybersécurité
