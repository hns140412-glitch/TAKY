param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$ClaudeArgs
)

$ErrorActionPreference = 'Stop'

$roots = New-Object System.Collections.Generic.List[string]

# Explicit least-privilege roots. G:\ is an external HDD, never infer it as Google Drive.
$fixedRoots = @(
  'D:\Git PWA',
  'G:\'
)
foreach ($root in $fixedRoots) {
  if (Test-Path $root) { $roots.Add($root) }
}

# Resolve the Desktop Drive folder without relying on non-ASCII script encoding.
$desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
$desktopDrive = Get-ChildItem -LiteralPath $desktopRoot -Directory -ErrorAction SilentlyContinue |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'TAKY_WORKSPACE') } |
  Select-Object -First 1 -ExpandProperty FullName
if ($desktopDrive) { $roots.Add($desktopDrive) }

# Google Drive for desktop: F:\ is the designated mount path.
# Add it only when the mount actually exists after reboot; never substitute G:\.
if (Test-Path 'F:\') {
  $roots.Add('F:\')
} else {
  Write-Host '[TAKY] Google Drive mount F:\ not present; skipped safely.'
}

# Never use provider API keys as fallback.
'ANTHROPIC_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY' | ForEach-Object {
  Remove-Item "Env:$_" -ErrorAction SilentlyContinue
}

$addDirArgs = @()
foreach ($r in ($roots | Select-Object -Unique)) {
  $addDirArgs += '--add-dir'
  $addDirArgs += $r
}

Write-Host ('[TAKY] Claude roots: ' + (($roots | Select-Object -Unique) -join ' | '))
& claude @addDirArgs @ClaudeArgs
exit $LASTEXITCODE
