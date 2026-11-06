param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$ClaudeArgs
)

$ErrorActionPreference = 'Stop'
$roots = New-Object System.Collections.Generic.List[string]

# Protected G: is an explicit TAKY source HOLD. Never test, scan or
# hand this entire drive to Claude as an unrestricted --add-dir root.
$fixedRoots = @(
  'D:\Git PWA'
)
foreach ($root in $fixedRoots) {
  if (Test-Path $root) { $roots.Add($root) }
}

$desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
$desktopDrive = Get-ChildItem -LiteralPath $desktopRoot -Directory -ErrorAction SilentlyContinue |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'TAKY_WORKSPACE') } |
  Select-Object -First 1 -ExpandProperty FullName
# Only the approved TAKY workspace itself, never the entire Desktop sync root.
if ($desktopDrive) { $roots.Add((Join-Path $desktopDrive 'TAKY_WORKSPACE')) }

# Project-scoped Cloud Drive access. Do not grant unrelated files on F:\.
$projectDrive = 'F:\내 드라이브\TAKY'
if (Test-Path -LiteralPath $projectDrive -PathType Container) {
  $roots.Add($projectDrive)
} else {
  Write-Host '[TAKY] TAKY project Drive folder unavailable; skipped safely.'
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
# Keep the parent Terminal pane alive even when TAKY_START calls exit.
# Run the existing launcher in a child PowerShell process; do not rewrite it.
& pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\TAKY_START.ps1" @addDirArgs @ClaudeArgs
$claudeExit = $LASTEXITCODE
if ($claudeExit -ne 0) {
  Write-Warning ("Claude CLI exited (code $claudeExit). Pane preserved for diagnosis.")
} else {
  Write-Host '[TAKY] Claude CLI ended. Pane remains open.' -ForegroundColor Yellow
}
