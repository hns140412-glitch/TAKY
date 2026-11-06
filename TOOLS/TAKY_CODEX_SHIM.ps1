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

# Distinguish local MCP configuration from model invocation. Fail closed for
# every MCP operation except read-only inspection and this user-approved,
# checksum-pinned Reason Network registration. No inference permission changes.
if ($first -eq 'mcp') {
  $sub = if ($CodexArgs.Count -ge 2) { [string]$CodexArgs[1] } else { '' }
  $mcpInspect = (
    ($sub -eq 'list' -and ($CodexArgs.Count -eq 2 -or
      ($CodexArgs.Count -eq 3 -and $CodexArgs[2] -eq '--json'))) -or
    ($sub -eq 'get' -and $CodexArgs.Count -eq 3 -and
      $CodexArgs[2] -match '^[a-zA-Z0-9_-]{1,80}$')
  )
  $reasonExe = Join-Path $env:LOCALAPPDATA 'TAKY\reason_network_evaluation\bin\reason-network.exe'
  $rnConfig = Join-Path $env:USERPROFILE '.reason\network\config.toml'
  # PowerShell drops an unquoted bare -- when forwarding to a .ps1 shim.
  # Accept only the two exact representations of the approved registration.
  $hasSeparator = ($CodexArgs.Count -eq 6 -and $CodexArgs[3] -ceq '--')
  $mcpApprovedAdd = (
    $sub -eq 'add' -and $CodexArgs[2] -ceq 'reason-network' -and
    (($hasSeparator -and $CodexArgs[4] -ceq $reasonExe -and $CodexArgs[5] -ceq 'mcp') -or
      ($CodexArgs.Count -eq 5 -and $CodexArgs[3] -ceq $reasonExe -and $CodexArgs[4] -ceq 'mcp'))
  )
  if ($mcpApprovedAdd) {
    $mcpApprovedAdd = (Test-Path -LiteralPath $reasonExe -PathType Leaf) -and
      (Test-Path -LiteralPath $rnConfig -PathType Leaf)
    if ($mcpApprovedAdd) {
      $mcpApprovedAdd = (
        (Get-FileHash -LiteralPath $reasonExe -Algorithm SHA256).Hash -eq
        'BD2466345825D3505D52069725DC5C87CF49B1B0CD31F1974896ACA9DE2A6A11'
      )
    }
    if ($mcpApprovedAdd) {
      $policy = Get-Content -LiteralPath $rnConfig -Raw
      $mcpApprovedAdd = (
        $policy -match '(?m)^auto_update\s*=\s*false\s*$' -and
        $policy -match '(?m)^default\s*=\s*"hold"\s*$' -and
        $policy -match '(?m)^share_unmanaged\s*=\s*false\s*$' -and
        $policy -match '(?m)^share_paths\s*=\s*false\s*$' -and
        $policy -match '(?m)^lan\s*=\s*false\s*$' -and
        $policy -match '(?m)^.D:\\.*=\s*"off"\s*$'
      )
    }
  }
  if ($mcpApprovedAdd) {
    # Reconstruct the native CLI separator lost in PowerShell script forwarding.
    & $realCodex mcp add reason-network -- $reasonExe mcp
    exit $LASTEXITCODE
  }
  if ($mcpInspect) {
    & $realCodex @CodexArgs
    exit $LASTEXITCODE
  }
  Write-Host 'TAKY MCP_CONFIG_HOLD: unapproved MCP management action or security profile.' -ForegroundColor Yellow
  exit 23
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
    status = 'CLI_STARTED'
    task_verified = $false
    provider_ack_attested = $false
    shell_alias_workaround = 'NOT_NEEDED'
  }
  $receipt | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $receiptPath

  # Fix only the child Codex process environment. WindowsApps pwsh.exe aliases
  # cannot run under some restricted Windows tokens (CreateProcessAsUserW: 5).
  # This does not disable the sandbox, change user PATH, or bypass policy hooks.
  $oldPath = $env:PATH
  $code = 1
  try {
    $pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    if ($pwsh -and ([string]$pwsh.Source -match '(?i)\\WindowsApps\\pwsh\.exe$')) {
      $env:PATH = (($oldPath -split ';' | Where-Object {
        $_ -and ($_ -notmatch '(?i)[\\/]WindowsApps(?:[\\/]|$)')
      }) -join ';')
      $receipt.shell_alias_workaround = 'PROCESS_LOCAL_ALIAS_EXCLUSION'
    }
    # Windows PowerShell 5.1 turns benign native stderr into a terminating
    # NativeCommandError when ErrorActionPreference is Stop. Codex writes
    # informational stdin diagnostics to stderr. Preserve those diagnostics
    # and assess actual CLI failure solely from its exit code.
    $nativeErrorPreference = $ErrorActionPreference
    try {
      $ErrorActionPreference = 'Continue'
      & $realCodex @CodexArgs
      $code = $LASTEXITCODE
    } finally {
      $ErrorActionPreference = $nativeErrorPreference
    }
  } finally {
    $env:PATH = $oldPath
  }

  # Exit 0 means the CLI process exited, NOT that its model review passed.
  # Model-level HOLD/FAIL and real receiver ACK require separate verified evidence.
  $receipt.status = if ($code -eq 0) { 'CLI_EXITED_RESULT_UNVERIFIED' } else { 'CLI_EXIT_NONZERO' }
  $receipt.exit_code = $code
  $receipt.finished_at = (Get-Date).ToString('o')
  $receipt | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $receiptPath
  exit $code
}

Write-Host 'TAKY REROUTE_REQUIRED: no task receipt and no explicit-user authorization found.' -ForegroundColor Yellow
Write-Host 'User-explicit execution should set TAKY_USER_EXPLICIT_AUTHORIZATION=1 and TAKY_USER_INTENT.' -ForegroundColor Cyan
Write-Host 'Otherwise use TAKY_CODEX.ps1 with PlanJson + InvocationJson.' -ForegroundColor Cyan
exit 23
