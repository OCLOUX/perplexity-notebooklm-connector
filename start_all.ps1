# start_all.ps1 - Démarrage tout-en-un : serveur MCP + ngrok
# Usage : powershell -ExecutionPolicy Bypass -File start_all.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Démarrage Perplexity → NotebookLM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverScript = Join-Path $scriptDir "mcp_server\mcp_server.py"

# Vérifier que le script serveur existe
if (-not (Test-Path $serverScript)) {
    Write-Host "❌ Fichier introuvable : $serverScript" -ForegroundColor Red
    Write-Host "   Êtes-vous dans le bon dossier ?" -ForegroundColor Yellow
    exit 1
}

# Vérifier si port 3000 déjà occupé
$portUsed = netstat -ano 2>$null | Select-String "127.0.0.1:3000.*LISTENING"
if ($portUsed) {
    Write-Host "⚠️  Port 3000 déjà utilisé. Le serveur MCP est peut-être déjà lancé." -ForegroundColor Yellow
    Write-Host "   Pour forcer le redémarrage, fermez d'abord l'autre fenêtre." -ForegroundColor Yellow
    Write-Host ""
} else {
    # Démarrer le serveur MCP dans une nouvelle fenêtre
    Write-Host "[1/2] Démarrage du serveur MCP..." -ForegroundColor White
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\mcp_server'; python mcp_server.py" -WindowStyle Normal
    Start-Sleep -Seconds 3

    # Vérifier que le serveur répond
    try {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:3000/health" -TimeoutSec 5 -UseBasicParsing
        if ($health.StatusCode -eq 200) {
            Write-Host "   ✅ Serveur MCP démarré (http://127.0.0.1:3000)" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ❌ Le serveur MCP n'a pas démarré correctement" -ForegroundColor Red
        Write-Host "   Vérifiez la fenêtre PowerShell qui vient de s'ouvrir." -ForegroundColor Yellow
        exit 1
    }
}

# Démarrer ngrok
Write-Host "[2/2] Démarrage de ngrok..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 127.0.0.1:3000" -WindowStyle Normal
Start-Sleep -Seconds 4

# Récupérer l'URL ngrok via l'API locale
try {
    $tunnels = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5 -UseBasicParsing
    $json = $tunnels.Content | ConvertFrom-Json
    $url = $json.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1 -ExpandProperty public_url
    if ($url) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ Tout est démarré !" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  URL ngrok HTTPS :" -ForegroundColor White
        Write-Host "  $url/mcp" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  👉 Copiez cette URL dans Perplexity Desktop :" -ForegroundColor White
        Write-Host "     Settings → MCP Servers → Add Server → URL" -ForegroundColor Gray
        Write-Host ""
        # Copier dans le presse-papiers
        "$url/mcp" | Set-Clipboard
        Write-Host "  📋 URL copiée dans le presse-papiers !" -ForegroundColor Cyan
    }
} catch {
    Write-Host ""
    Write-Host "  ✅ ngrok démarré - vérifiez l'URL dans la fenêtre ngrok" -ForegroundColor Green
    Write-Host "  Ou ouvrez : http://127.0.0.1:4040" -ForegroundColor Gray
}

Write-Host ""
