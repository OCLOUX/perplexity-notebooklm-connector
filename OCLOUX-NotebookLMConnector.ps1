# OCLOUX-NotebookLMConnector.ps1 - Installation automatique du connecteur Perplexity -> NotebookLM
# Usage : powershell -ExecutionPolicy Bypass -File OCLOUX-NotebookLMConnector.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Perplexity -> NotebookLM Connector" -ForegroundColor Cyan
Write-Host "  Script d'installation automatique" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ok = $true

# --- 1. Python ---
Write-Host "[1/4] Verification de Python..." -NoNewline
try {
    $pyver = python --version 2>&1
    Write-Host " OK ($pyver)" -ForegroundColor Green
} catch {
    Write-Host " MANQUANT" -ForegroundColor Red
    Write-Host "  -> Telecharger : https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  -> IMPORTANT : cochez 'Add Python to PATH' lors de l'installation" -ForegroundColor Yellow
    $ok = $false
}

# --- 2. ngrok ---
Write-Host "[2/4] Verification de ngrok..." -NoNewline
try {
    $ngrokver = ngrok version 2>&1
    Write-Host " OK ($ngrokver)" -ForegroundColor Green
} catch {
    Write-Host " MANQUANT" -ForegroundColor Red
    Write-Host "  -> Telecharger : https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "  -> Puis : ngrok config add-authtoken VOTRE_TOKEN" -ForegroundColor Yellow
    $ok = $false
}

# --- 3. nlm ---
Write-Host "[3/4] Verification de nlm (NotebookLM CLI)..." -NoNewline
try {
    $nlmver = nlm --version 2>&1
    Write-Host " OK ($nlmver)" -ForegroundColor Green
} catch {
    Write-Host " MANQUANT - Installation en cours..." -ForegroundColor Yellow
    pip install notebooklm-cli
    Write-Host "  -> nlm installe. Lancez : nlm auth login" -ForegroundColor Yellow
}

# --- 4. Authentification NotebookLM ---
Write-Host "[4/4] Verification authentification NotebookLM..." -NoNewline
try {
    $notebooks = nlm notebook list 2>&1
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " NON CONNECTE" -ForegroundColor Yellow
    Write-Host "  -> Lancez : nlm auth login" -ForegroundColor Yellow
    $ok = $false
}

Write-Host ""
if ($ok) {
    Write-Host "OK Installation reussie ! Lancement des tests..." -ForegroundColor Green
    Write-Host ""
    powershell -ExecutionPolicy Bypass -File test_connection.ps1
} else {
    Write-Host "ATTENTION Corrigez les erreurs ci-dessus puis relancez OCLOUX-NotebookLMConnector.ps1" -ForegroundColor Yellow
}
