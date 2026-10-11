param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$ClaudeArgs
)

chcp 65001 > $null
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$ErrorActionPreference = 'Stop'
$repo = 'D:\Git PWA\TAKY'
$vault = 'D:\Git PWA\TAKY-SOURCE-VAULT'
$live = Join-Path $env:APPDATA 'TAKY\TAKY_LIVE.log'
New-Item -ItemType Directory -Force -Path (Split-Path $live) | Out-Null
Set-Location $repo

'ANTHROPIC_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY' | ForEach-Object {
  Remove-Item "Env:$_" -ErrorAction SilentlyContinue
}

$ghDir = 'C:\Program Files\GitHub CLI'
if ((Test-Path $ghDir) -and (($env:Path -split ';') -notcontains $ghDir)) {
  $env:Path += ';' + $ghDir
}

$host.UI.RawUI.WindowTitle = 'TAKY | Claude 최적 실행'
Write-Host 'TAKY Claude 최적 실행' -ForegroundColor Green
Write-Host '자연어 입력 -> 최소 컨텍스트/스킬 라우팅 -> 구현 -> 검증' -ForegroundColor Cyan
Write-Host 'OAuth/구독 로그인은 Claude CLI 자체 판정 사용 / API-key fallback 차단' -ForegroundColor DarkGray
Add-Content -LiteralPath $live -Value ('['+(Get-Date -Format 'HH:mm:ss')+':START] Claude 최적 실행 시작') -Encoding UTF8

& claude --model claude-sonnet-5-5 --add-dir $vault @ClaudeArgs
exit $LASTEXITCODE
