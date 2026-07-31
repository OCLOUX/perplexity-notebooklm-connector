param(
    [Parameter(Mandatory=$true)][string]$Title,
    [string]$SourceTitle = "Perplexity import",
    [switch]$Open
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $scriptDir "perplexity_to_notebooklm.py"

if ($Open) {
    Get-Clipboard | python $py --title $Title --source-title $SourceTitle --open
} else {
    Get-Clipboard | python $py --title $Title --source-title $SourceTitle
}
