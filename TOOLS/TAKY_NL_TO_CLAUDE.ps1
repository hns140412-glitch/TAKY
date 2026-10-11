param(
  [Parameter(Mandatory=$true,Position=0)]
  [string]$InputText,
  [string]$Mode='execute'
)

$ErrorActionPreference='Stop'

function Compress-TakyPrompt([string]$t) {
  $x = $t.Trim()
  $rules = @(
    @{p='(?i)확인 필요할 ?때까지.*'; r=''},
    @{p='(?i)쭉 진행해'; r=''},
    @{p='(?i)알아서'; r=''},
    @{p='(?i)잘'; r=''},
    @{p='(?i)제대로'; r=''},
    @{p='(?i)계속'; r=''},
    @{p='(?i)진행해'; r=''}
  )
  foreach($rule in $rules){ $x=[regex]::Replace($x,$rule.p,$rule.r) }
  $x=[regex]::Replace($x,'\s+',' ').Trim()
  return $x
}

$compressed = Compress-TakyPrompt $InputText

$prompt = @"
TAKY EXECUTION REQUEST
GOAL: $compressed

AUTHORITY:
- Current user instruction
- TAKY.md / CLAUDE.md
- Current C2S/HANDOFF authority for the target area

DEFAULT EXECUTION RULES:
- USER != DEBUGGER
- Compare -> Review -> Improve -> Optimize -> Verify
- Prefer smallest sufficient diff
- Read current state before changing
- Preserve CLOSED/PASS; act on OPEN only when applicable
- No paid/provider API-key fallback
- No deploy/push/merge/release without explicit approval
- Access failure != source absence
- BLOCKED != FAILED

VALIDATION:
- syntax/static checks
- runtime/error checks where safe
- self-review
- regression verification
- report only evidence-backed PASS/FAIL/HOLD

OUTPUT:
- RESULT
- CHANGED
- TESTS
- REMAINING OPEN
"@

Write-Host '=== TAKY COMPRESSED ===' -ForegroundColor Green
Write-Host $compressed
Write-Host '=== CLAUDE PROMPT ===' -ForegroundColor Cyan
Write-Output $prompt

if($Mode -eq 'preview'){ exit 0 }

$env:ANTHROPIC_API_KEY=$null
$env:OPENAI_API_KEY=$null
$env:GEMINI_API_KEY=$null
$env:GOOGLE_API_KEY=$null

Set-Location 'D:\Git PWA\TAKY'
& "$PSScriptRoot\\TAKY_START.ps1" $prompt
