# test_connection.ps1 - Tests complets de connexion
# Usage : powershell -ExecutionPolicy Bypass -File test_connection.ps1

$ErrorActionPreference = "SilentlyContinue"
$pass = 0
$fail = 0

function Test-OK($label) {
    Write-Host ("  ✅ " + $label) -ForegroundColor Green
    $global:pass++
}
function Test-FAIL($label, $hint) {
    Write-Host ("  ❌ " + $label) -ForegroundColor Red
    if ($hint) { Write-Host ("     → " + $hint) -ForegroundColor Yellow }
    $global:fail++
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Tests de connexion - MCP NotebookLM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Test 1 : Python ---
Write-Host "[1/6] Python" -ForegroundColor White
try {
    $v = python --version 2>&1
    if ($v -match "Python") { Test-OK $v }
    else { Test-FAIL "Python non trouvé" "Installer Python depuis https://www.python.org/downloads/ (cocher 'Add to PATH')" }
} catch {
    Test-FAIL "Python non trouvé" "Installer Python depuis https://www.python.org/downloads/"
}

# --- Test 2 : ngrok ---
Write-Host "[2/6] ngrok" -ForegroundColor White
try {
    $v = ngrok version 2>&1
    if ($v -match "ngrok") { Test-OK $v }
    else { Test-FAIL "ngrok non trouvé" "Installer depuis https://ngrok.com/download" }
} catch {
    Test-FAIL "ngrok non trouvé" "Installer depuis https://ngrok.com/download"
}

# --- Test 3 : nlm ---
Write-Host "[3/6] nlm (NotebookLM CLI)" -ForegroundColor White
try {
    $v = nlm --version 2>&1
    if ($LASTEXITCODE -eq 0 -or $v) { Test-OK "nlm disponible" }
    else { Test-FAIL "nlm non trouvé" "pip install notebooklm-cli" }
} catch {
    Test-FAIL "nlm non trouvé" "pip install notebooklm-cli"
}

# --- Test 4 : Authentification NotebookLM ---
Write-Host "[4/6] Authentification NotebookLM" -ForegroundColor White
try {
    $notebooks = nlm notebook list 2>&1
    if ($LASTEXITCODE -eq 0) {
        $count = ($notebooks | Measure-Object -Line).Lines
        Test-OK "Connecté ($count entrées trouvées)"
    } else {
        Test-FAIL "Non authentifié" "Lancer : nlm auth login"
    }
} catch {
    Test-FAIL "Erreur nlm" "Lancer : nlm auth login"
}

# --- Test 5 : Serveur MCP ---
Write-Host "[5/6] Serveur MCP (port 3000)" -ForegroundColor White

# Vérifier si déjà en cours
$already = netstat -ano 2>$null | Select-String ":3000"
if ($already) {
    Write-Host "     (serveur déjà en cours d'écoute)" -ForegroundColor Gray
} else {
    # Démarrer temporairement
    $proc = Start-Process python -ArgumentList "mcp_server\mcp_server.py" -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:3000/health" -TimeoutSec 5 -UseBasicParsing 2>&1
    if ($resp.StatusCode -eq 200) {
        $json = $resp.Content | ConvertFrom-Json
        Test-OK "Serveur OK - version $($json.version)"
    } else {
        Test-FAIL "Serveur répond $($resp.StatusCode)" "Vérifier mcp_server.py"
    }
} catch {
    Test-FAIL "Serveur MCP inaccessible sur http://127.0.0.1:3000" "Lancer : python mcp_server\mcp_server.py"
}

# Arrêter le serveur temporaire si on l'a démarré
if ($proc) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }

# --- Test 6 : Protocole MCP JSON-RPC ---
Write-Host "[6/6] Protocole MCP (JSON-RPC initialize)" -ForegroundColor White

# Redémarrer pour ce test
$proc2 = Start-Process python -ArgumentList "mcp_server\mcp_server.py" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

try {
    $body = '{"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"jsonrpc":"2.0","id":0}'
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:3000/mcp" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 5 `
        -UseBasicParsing 2>&1
    if ($resp.StatusCode -eq 200) {
        $json = $resp.Content | ConvertFrom-Json
        $sid = $resp.Headers["Mcp-Session-Id"]
        Test-OK "initialize OK - version=$($json.result.protocolVersion) session=$sid"
    } else {
        Test-FAIL "Protocole MCP répond $($resp.StatusCode)" "Vérifier les logs de mcp_server.py"
    }
} catch {
    Test-FAIL "Protocole MCP inaccessible" "Vérifier que mcp_server.py tourne"
}

if ($proc2) { Stop-Process -Id $proc2.Id -Force -ErrorAction SilentlyContinue }

# --- Résumé ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($fail -eq 0) {
    Write-Host "  ✅ Tous les tests passent ($pass/6)" -ForegroundColor Green
    Write-Host "  Prochaine étape : powershell -File start_all.ps1" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  $pass réussis, $fail échoués" -ForegroundColor Yellow
    Write-Host "  Corrigez les erreurs avant de continuer." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
