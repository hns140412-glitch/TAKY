param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$ClaudeArgs
)

$ErrorActionPreference = 'Stop'
$roots = New-Object System.Collections.Generic.List[string]

$fixedRoots = @(
  'D:\Git PWA',
  'G:\'
)
foreach ($root in $fixedRoots) {
  if (Test-Path $root) { $roots.Add($root) }
}

$desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
$desktopDrive = Get-ChildItem -LiteralPath $desktopRoot -Directory -ErrorAction SilentlyContinue |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'TAKY_WORKSPACE') } |
  Select-Object -First 1 -ExpandProperty FullName
if ($desktopDrive) { $roots.Add($desktopDrive) }

if (Test-Path 'F:\') {
  $roots.Add('F:\')
} else {
  Write-Host '[TAKY] Google Drive mount F:\ not present; skipped safely.'
}

'ANTHROPIC_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY' | ForEach-Object {
  Remove-Item "Env:$_" -ErrorAction SilentlyContinue
}

$addDirArgs = @()
foreach ($r in ($roots | Select-Object -Unique)) {
  $addDirArgs += '--add-dir'
  $addDirArgs += $r
}

Write-Host ('[TAKY] Claude roots: ' + (($roots | Select-Object -Unique) -join ' | '))
& "$PSScriptRoot\TAKY_START.ps1" @addDirArgs @ClaudeArgs
exit $LASTEXITCODE
