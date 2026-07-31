# OCLOUX-NotebookLMConnector-start.ps1 - Demarrage tout-en-un : serveur MCP + ngrok
# Usage : powershell -ExecutionPolicy Bypass -File OCLOUX-NotebookLMConnector-start.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Demarrage Perplexity -> NotebookLM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverScript = Join-Path $scriptDir "mcp_server\mcp_server.py"

# Verifier que le script serveur existe
if (-not (Test-Path $serverScript)) {
    Write-Host "ERREUR Fichier introuvable : $serverScript" -ForegroundColor Red
    Write-Host "   Etes-vous dans le bon dossier ?" -ForegroundColor Yellow
    exit 1
}

# Verifier si port 3000 deja occupe
$portUsed = netstat -ano 2>$null | Select-String "127.0.0.1:3000.*LISTENING"
if ($portUsed) {
    Write-Host "ATTENTION Port 3000 deja utilise. Le serveur MCP est peut-etre deja lance." -ForegroundColor Yellow
    Write-Host "   Pour forcer le redemarrage, fermez d'abord l'autre fenetre." -ForegroundColor Yellow
    Write-Host ""
} else {
    # Demarrer le serveur MCP dans une nouvelle fenetre
    Write-Host "[1/2] Demarrage du serveur MCP..." -ForegroundColor White
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\mcp_server'; python mcp_server.py" -WindowStyle Normal
    Start-Sleep -Seconds 3

    # Verifier que le serveur repond
    try {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:3000/health" -TimeoutSec 5 -UseBasicParsing
        if ($health.StatusCode -eq 200) {
            Write-Host "   OK Serveur MCP demarre (http://127.0.0.1:3000)" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ERREUR Le serveur MCP n'a pas demarre correctement" -ForegroundColor Red
        Write-Host "   Verifiez la fenetre PowerShell qui vient de s'ouvrir." -ForegroundColor Yellow
        exit 1
    }
}

# Demarrer ngrok
Write-Host "[2/2] Demarrage de ngrok..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 127.0.0.1:3000" -WindowStyle Normal
Start-Sleep -Seconds 4

# Recuperer l'URL ngrok via l'API locale
try {
    $tunnels = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5 -UseBasicParsing
    $json = $tunnels.Content | ConvertFrom-Json
    $url = $json.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1 -ExpandProperty public_url
    if ($url) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  OK Tout est demarre !" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  URL ngrok HTTPS :" -ForegroundColor White
        Write-Host "  $url/mcp" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  >> Copiez cette URL dans Perplexity Desktop :" -ForegroundColor White
        Write-Host "     Settings -> MCP Servers -> Add Server -> URL" -ForegroundColor Gray
        Write-Host ""
        # Copier dans le presse-papiers
        "$url/mcp" | Set-Clipboard
        Write-Host "  CLIPBOARD URL copiee dans le presse-papiers !" -ForegroundColor Cyan
    }
} catch {
    Write-Host ""
    Write-Host "  OK ngrok demarre - verifiez l'URL dans la fenetre ngrok" -ForegroundColor Green
    Write-Host "  Ou ouvrez : http://127.0.0.1:4040" -ForegroundColor Gray
}

Write-Host ""
