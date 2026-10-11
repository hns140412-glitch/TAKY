param(
  [ValidateSet('codex','gemini','claude')][string]$Provider,
  [Parameter(Mandatory=$true)][string]$Prompt,
  [string]$Repo = 'D:\Git PWA\TAKY',
  [ValidateSet('Envelope','Raw')][string]$OutputMode = 'Envelope',
  [ValidateSet('text','json')][string]$ClaudeOutputFormat = 'text',
  [int]$ClaudeMaxTurns = 24,
  [string]$ReceiptOut,
  [switch]$UseAppCodex
)
$ErrorActionPreference = 'Stop'
$orch = 'D:\Git PWA\TAKY-2.0-ORCH'
$env:PYTHONPATH = $orch
$env:OPENAI_API_KEY = $null
$env:ANTHROPIC_API_KEY = $null
$env:GEMINI_API_KEY = $null
$env:GOOGLE_API_KEY = $null
Set-Location $Repo
$realCodex='C:\Users\YKH_1507-03\AppData\Roaming\npm\codex.cmd'
$appCodex='C:\Users\YKH_1507-03\AppData\Local\OpenAI\Codex\bin\13995fba801849b0\codex.exe'

if ($Provider -eq 'codex') {
  $status = (& $realCodex login status 2>&1 | Out-String)
  if ($status -notmatch 'ChatGPT') { Write-Output 'TAKY_CROSS_REVIEW_AUTH_REQUIRED'; exit 20 }
  $model='codex'; $providerName='openai'
  if ($UseAppCodex) {
    $routeTool='codex-app-devnull'
    $codexBinary=$appCodex
  } else {
    $routeTool='codex-ephemeral'
    $codexBinary=$realCodex
  }
  $argv=@(
    $codexBinary,'exec',
    '--sandbox','read-only',
    '--ephemeral',
    '--ignore-user-config',
    '--color','never',
    '-C',$Repo,
    $Prompt
  )
} elseif ($Provider -eq 'claude') {
  try {
    $auth = (& claude auth status 2>$null | Out-String | ConvertFrom-Json)
  } catch {
    $auth = $null
  }
  if (-not $auth -or -not $auth.loggedIn -or $auth.authMethod -ne 'oauth_token') {
    Write-Output 'TAKY_CROSS_REVIEW_AUTH_REQUIRED: Claude OAuth subscription auth is not verified.'
    exit 20
  }
  $model='sonnet'; $providerName='anthropic'; $routeTool='claude'
  $argv=@(
    'claude','--safe-mode','-p',$Prompt,
    '--output-format',$ClaudeOutputFormat,
    '--model','sonnet',
    '--no-session-persistence',
    '--max-turns',([string]$ClaudeMaxTurns),
    '--tools','Read','Grep','Glob'
  )
} else {
  if (-not (Get-Command gemini -ErrorAction SilentlyContinue)) { Write-Output 'TAKY_CROSS_REVIEW_NOT_AVAILABLE'; exit 21 }
  $model='gemini'; $providerName='google'; $routeTool='gemini'
  $argv=@('gemini','--approval-mode','plan','--output-format','text','--prompt',$Prompt)
}

$temp=Join-Path $env:TEMP ('taky-review-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $temp | Out-Null
try {
  $call=@{
    model=$model; effort='medium'; context='delta'; expected_calls=1
    dry_run_plan=@{
      expected_calls=1
      operations=@('one bounded independent review invocation')
      batch_strategy='single-review-batch'
      fallback='HOLD'
      paid_api=$false
    }
  }
  $plan=@{
    task_id='external-review-'+[guid]::NewGuid().ToString('N')
    action_id='review:external-model'
    context=@{mode='delta'}
    attempt=@{target=$Repo;method_or_tool=$routeTool}
    call=$call
  }
  $planPath=Join-Path $temp 'plan.json'
  $plan | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $planPath -Encoding UTF8
  $preErrPath=Join-Path $temp 'preflight.stderr.txt'
  $preText=(& python -m TAKY2.orchestrator preflight $planPath 2> $preErrPath | Out-String)
  $preCode=$LASTEXITCODE
  $preErr=if (Test-Path -LiteralPath $preErrPath) { Get-Content -LiteralPath $preErrPath -Raw } else { '' }
  Write-Output '[TAKY_DRY_RUN_PLAN] preflight completed'
  if ($preCode -ne 0) {
    Write-Output $preText
    if ($preErr) { [Console]::Error.Write($preErr) }
    exit $preCode
  }
  try {
    $pre=$preText | ConvertFrom-Json
  } catch {
    Write-Output 'TAKY_REVIEW_WRAPPER_PARSE_ERROR: preflight stdout was not valid JSON.'
    if ($preErr) { [Console]::Error.Write($preErr) }
    exit 25
  }
  if (-not $pre.allowed -or -not $pre.call_allowed -or -not $pre.receipt_id) { Write-Output $preText; exit 22 }

  $inv=@{provider=$providerName;method_or_tool=$routeTool;call=$call;argv=$argv}
  $invPath=Join-Path $temp 'invocation.json'
  $inv | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $invPath -Encoding UTF8
  $execErrPath=Join-Path $temp 'execute.stderr.txt'
  $execText=(& python -m TAKY2.orchestrator execute $pre.receipt_id $invPath --executor-id ('TAKY_MODEL_REVIEW_'+$Provider.ToUpper()) 2> $execErrPath | Out-String)
  $execCode=$LASTEXITCODE
  $execErr=if (Test-Path -LiteralPath $execErrPath) { Get-Content -LiteralPath $execErrPath -Raw } else { '' }
  if ($execCode -ne 0) {
    Write-Output $execText
    if ($execErr) { [Console]::Error.Write($execErr) }
    exit $execCode
  }
  try {
    $exec=$execText | ConvertFrom-Json
  } catch {
    & python -m TAKY2.orchestrator record-failure $pre.receipt_id ENVIRONMENT | Out-Null
    Write-Output 'TAKY_REVIEW_WRAPPER_PARSE_ERROR: execute stdout was not valid JSON; receipt released as ENVIRONMENT.'
    if ($execErr) { [Console]::Error.Write($execErr) }
    exit 25
  }
  if ($ReceiptOut) {
    @{receipt_id=$pre.receipt_id; provider=$Provider; executor_state=$exec.state} |
      ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ReceiptOut -Encoding UTF8
  }
  if ($OutputMode -eq 'Raw') {
    if ($null -ne $exec.result.stdout) { [Console]::Out.Write([string]$exec.result.stdout) }
    if ($null -ne $exec.result.stderr -and [string]$exec.result.stderr) { [Console]::Error.Write([string]$exec.result.stderr) }
  } else {
    Write-Output $execText
  }
  if ($null -ne $exec.result.returncode -and [int]$exec.result.returncode -ne 0) {
    $rc = [int]$exec.result.returncode
    if ($rc -eq 124) {
      & python -m TAKY2.orchestrator record-failure $pre.receipt_id ENVIRONMENT | Out-Null
    }
    exit $rc
  }
  exit 0
}
finally {
  Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
