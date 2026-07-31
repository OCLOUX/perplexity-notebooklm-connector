$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:MCP_PORT = "3000"
Write-Host "Serveur MCP NotebookLM sur http://localhost:3000/mcp" -ForegroundColor Green
Write-Host "Laissez cette fenêtre ouverte pendant l'utilisation avec Perplexity." -ForegroundColor Yellow
python "$scriptDir\mcp_server.py"
