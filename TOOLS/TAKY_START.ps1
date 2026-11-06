chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$ErrorActionPreference = 'Stop'
$repo = 'D:\Git PWA\TAKY'
$vault = 'D:\Git PWA\TAKY-SOURCE-VAULT'
$live = Join-Path $env:APPDATA 'TAKY\TAKY_LIVE.log'
New-Item -ItemType Directory -Force -Path (Split-Path $live) | Out-Null
Set-Location $repo

# SAVEY guard: subscription/OAuth only inside the TAKY shell.
$env:ANTHROPIC_API_KEY = $null
$env:OPENAI_API_KEY = $null
$env:GEMINI_API_KEY = $null
$env:GOOGLE_API_KEY = $null

# Keep GitHub CLI available in this shell even if Windows Terminal started before PATH refresh.
$ghDir = 'C:\Program Files\GitHub CLI'
if ((Test-Path $ghDir) -and (($env:Path -split ';') -notcontains $ghDir)) {
  $env:Path += ';' + $ghDir
}

$host.UI.RawUI.WindowTitle = 'TAKY | Claude 최적 실행'
Write-Host 'TAKY Claude 최적 실행' -ForegroundColor Green
Write-Host '자연어 입력 -> 최소 컨텍스트/스킬 라우팅 -> 구현 -> 검증' -ForegroundColor Cyan
Add-Content -LiteralPath $live -Value ('['+(Get-Date -Format 'HH:mm:ss')+':START] Claude 최적 실행 시작') -Encoding UTF8

try {
  $auth = (& claude auth status 2>$null | Out-String | ConvertFrom-Json)
} catch {
  $auth = $null
}
if (-not $auth -or -not $auth.loggedIn -or $auth.authMethod -ne 'oauth_token') {
  Write-Warning 'SAVEY BLOCK: Claude Code OAuth subscription auth is not verified. API-key fallback remains disabled.'
  Write-Host 'Fix with: claude auth login'
  return
}

Add-Content -LiteralPath $live -Value ('['+(Get-Date -Format 'HH:mm:ss')+':PASS] OAuth 확인 / API-key fallback 차단 / intent-router 활성') -Encoding UTF8
& claude --model claude-sonnet-5-5 --add-dir $vault

