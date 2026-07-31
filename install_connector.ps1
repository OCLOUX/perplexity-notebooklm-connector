$target = "C:\IA\notebooklm-mcp\perplexity-notebooklm-connector"
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -Force .\perplexity_to_notebooklm.py $target
Copy-Item -Force .\run_from_clipboard.ps1 $target
Write-Host "Installé dans $target"
Write-Host ""
Write-Host "Test direct :"
Write-Host 'python .\perplexity_to_notebooklm.py --title "Test Perplexity" --text "Bonjour" --open'
Write-Host ""
Write-Host "Depuis le presse-papiers :"
Write-Host '.\run_from_clipboard.ps1 -Title "Veille cybersécurité" -Open'
