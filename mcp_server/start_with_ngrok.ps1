param([int]$Port = 3000)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Démarrage du serveur MCP en arrière-plan..." -ForegroundColor Cyan
$serverJob = Start-Job -ScriptBlock {
    param($dir, $port)
    $env:MCP_PORT = $port
    python "$dir\mcp_server.py"
} -ArgumentList $scriptDir, $Port
Start-Sleep -Seconds 2
Write-Host "Tunnel ngrok sur le port $Port..." -ForegroundColor Cyan
Write-Host "Copiez l'URL https://....ngrok-free.app/mcp dans Perplexity Desktop -> Connecteurs" -ForegroundColor Yellow
ngrok http $Port
