param(
  [ValidateSet('codex','gemini')][string]$Provider,
  [Parameter(Mandatory=$true)][string]$Prompt,
  [string]$Repo = 'D:\Git PWA\TAKY'
)

$ErrorActionPreference = 'Stop'

# SAVEY: never let provider API keys silently override subscription/OAuth auth.
$env:OPENAI_API_KEY = $null
$env:ANTHROPIC_API_KEY = $null
$env:GEMINI_API_KEY = $null
$env:GOOGLE_API_KEY = $null

Set-Location $Repo

if ($Provider -eq 'codex') {
  $status = (& codex login status 2>&1 | Out-String)
  if ($status -notmatch 'ChatGPT') {
    Write-Output 'TAKY_CROSS_REVIEW_AUTH_REQUIRED: Codex is not logged in with ChatGPT.'
    exit 20
  }
  & codex exec --sandbox read-only -C $Repo $Prompt
  exit $LASTEXITCODE
}
if ($Provider -eq 'gemini') {
  if (-not (Get-Command gemini -ErrorAction SilentlyContinue)) {
    Write-Output 'TAKY_CROSS_REVIEW_NOT_AVAILABLE: Gemini CLI is not installed.'
    exit 21
  }
  # Google OAuth is required by TAKY. Never fall back to GEMINI_API_KEY.
  & gemini --approval-mode plan --output-format text --prompt $Prompt
  if ($LASTEXITCODE -ne 0) {
    Write-Output 'TAKY_CROSS_REVIEW_AUTH_OR_RUNTIME_REQUIRED: configure Google OAuth; API-key fallback is disabled.'
  }
  exit $LASTEXITCODE
}
