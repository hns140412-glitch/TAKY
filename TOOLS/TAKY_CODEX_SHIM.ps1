$CodexArgs = @($args)
$ErrorActionPreference='Stop'
$realCodex='C:\Users\YKH_1507-03\AppData\Roaming\npm\codex.cmd'
$canonical='D:\Git PWA\TAKY\TOOLS\TAKY_CODEX.ps1'
$receiptPath='D:\Git PWA\TAKY\CURRENT\EXECUTION\CODEX_USER_AUTH_CURRENT.json'

$first = if ($CodexArgs.Count -gt 0) { [string]$CodexArgs[0] } else { '' }
$passthrough = @('login','logout','--version','-V','--help','help')
if ($first -in $passthrough) {
  & $realCodex @CodexArgs
  exit $LASTEXITCODE
}

if ($env:TAKY_PLAN_JSON -and $env:TAKY_INVOCATION_JSON) {
  & $canonical -PlanJson $env:TAKY_PLAN_JSON -InvocationJson $env:TAKY_INVOCATION_JSON -ExecutorId 'TAKY_CODEX_CLI'
  exit $LASTEXITCODE
}

# TAKY rule: explicit user direction authorizes execution and outranks internal ROUTE/NECESSITY/COST blocking.
# Authorization is NOT a command to multiply tools, agents, retries, or paid calls.
# TAKY should still choose the minimum sufficient route: one bounded executor first, add reviewers only when
# the user explicitly asks or independent verification is materially needed. This does not override
# OS/security/platform safety constraints.
if ($env:TAKY_USER_EXPLICIT_AUTHORIZATION -eq '1') {
  $dir = Split-Path -Parent $receiptPath
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $receipt = [ordered]@{
    schema_version = 'TAKY_USER_EXPLICIT_EXECUTION_RECEIPT_V1'
    executor = 'CODEX'
    authorization = 'USER_EXPLICIT'
    route = 'DIRECT_CODEX_CLI'
    user_intent = if ($env:TAKY_USER_INTENT) { $env:TAKY_USER_INTENT } else { 'EXPLICIT_CODEX_USE' }
    arguments = @($CodexArgs)
    started_at = (Get-Date).ToString('o')
    status = 'STARTED'
  }
  $receipt | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $receiptPath
  & $realCodex @CodexArgs
  $code = $LASTEXITCODE
  $receipt.status = if ($code -eq 0) { 'COMPLETED' } else { 'FAILED' }
  $receipt.exit_code = $code
  $receipt.finished_at = (Get-Date).ToString('o')
  $receipt | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $receiptPath
  exit $code
}

Write-Host 'TAKY REROUTE_REQUIRED: no task receipt and no explicit-user authorization found.' -ForegroundColor Yellow
Write-Host 'User-explicit execution should set TAKY_USER_EXPLICIT_AUTHORIZATION=1 and TAKY_USER_INTENT.' -ForegroundColor Cyan
Write-Host 'Otherwise use TAKY_CODEX.ps1 with PlanJson + InvocationJson.' -ForegroundColor Cyan
exit 23
