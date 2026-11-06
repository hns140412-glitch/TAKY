param(
  [ValidateSet('codex','gemini','claude')][string]$Provider,
  [Parameter(Mandatory=$true)][string]$Prompt,
  [string]$TaskId = '',
  [string]$Repo = 'D:\Git PWA\TAKY',
  [ValidateSet('Envelope','Raw')][string]$OutputMode = 'Envelope',
  [ValidateSet('text','json')][string]$ClaudeOutputFormat = 'text',
  [int]$ClaudeMaxTurns = 24,
  [string]$ReceiptOut,
  [switch]$UseAppCodex,
  [string]$CouncilBindingJson = '',
  [string]$TargetReceiptId = '',
  [string]$ScopedEditTaskSha256 = ''
)
$ErrorActionPreference = 'Stop'
$orch = 'D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH'
$env:PYTHONPATH = $orch
$env:OPENAI_API_KEY = $null
$env:ANTHROPIC_API_KEY = $null
$env:GEMINI_API_KEY = $null
$env:GOOGLE_API_KEY = $null
# TAKY2 bridge implements bounded Claude/Codex review only. Unsupported routing
# must return a concrete error before login, packet building, or preflight.
if ($Provider -eq 'gemini') {
  Write-Output 'TAKY_GEMINI_REVIEW_ROUTE_UNSUPPORTED: no governed Gemini executor in TAKY2; no model call attempted.'
  exit 21
}
Set-Location $Repo
$realCodex='C:\Users\YKH_1507-03\AppData\Roaming\npm\codex.cmd'
$appCodex='C:\Users\YKH_1507-03\AppData\Local\OpenAI\Codex\bin\13995fba801849b0\codex.exe'

if ($Provider -eq 'codex') {
  # codex.cmd can emit "Logged in using ChatGPT" on stderr. With
  # ErrorActionPreference=Stop, PowerShell turns that into a terminating
  # NativeCommandError even when the auth process exits successfully.
  # Merge stderr into stdout inside cmd.exe before PowerShell sees it.
  $loginCommand='"' + $realCodex + '" login status 2>&1'
  $status = (& cmd.exe /d /s /c $loginCommand | Out-String)
  if ($LASTEXITCODE -ne 0 -or $status -notmatch 'ChatGPT') {
    Write-Output 'TAKY_CROSS_REVIEW_AUTH_REQUIRED'; exit 20
  }
  $model='codex'; $providerName='openai'
  if ($UseAppCodex) {
    $routeTool='codex-app-devnull'
    $codexBinary=$appCodex
  } else {
    # TAKY2 CODEX_VERIFY_ONLY requires actual_tool='codex'; codex-ephemeral is a preflight/bridge mismatch.
    $routeTool='codex'
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
  # Resolve the installed subscription CLI without PATH-based executable selection.
  $claudeBinary=Join-Path $HOME '.local\bin\claude.exe'
  if(-not (Test-Path -LiteralPath $claudeBinary -PathType Leaf)){
    Write-Output 'TAKY_CLAUDE_PINNED_CLI_NOT_FOUND'; exit 21
  }
  try {
    $auth = (& $claudeBinary auth status 2>$null | Out-String | ConvertFrom-Json)
  } catch {
    $auth = $null
  }
  if (-not $auth -or -not $auth.loggedIn -or $auth.authMethod -notin @('claude.ai','oauth_token')) {
    Write-Output 'TAKY_CROSS_REVIEW_AUTH_REQUIRED: Claude OAuth subscription auth is not verified.'
    exit 20
  }
  $model='sonnet'; $providerName='anthropic'; $routeTool='claude'
  $argv=@(
    $claudeBinary,'--safe-mode','-p',$Prompt,
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
  # Bind a compact, immutable packet before asking TAKY2 for model approval.
  # The backend allows only PACKET_ONLY Claude or CODEX_VERIFY_ONLY Codex.
  if($Provider -notin @('claude','codex')){throw 'PACKET_ONLY_EXECUTOR_NOT_AVAILABLE'}
  if($Prompt.Length -gt 2500){throw 'REVIEW_PROMPT_TOO_LARGE'}
  $promptFile=Join-Path $temp 'prompt.json'
  $packetFile=Join-Path $temp 'packet.txt'
  @{prompt=$Prompt}|ConvertTo-Json -Depth 3|Set-Content -LiteralPath $promptFile -Encoding UTF8
  $packetTool='D:\Git PWA\TAKY\TOOLS\TAKY_MODEL_REVIEW_PACKET.py'
  $taskSkillMode=if($OutputMode -eq 'Raw'){'implementation'}else{'review'}
  $packetRaw=(& python -X utf8 $packetTool --repo $Repo --prompt-file $promptFile --packet-file $packetFile --mode $taskSkillMode | Out-String)
  if($LASTEXITCODE -ne 0){throw 'REVIEW_PACKET_BUILD_FAILED'}
  $packetMeta=$packetRaw|ConvertFrom-Json
  if(!$packetMeta.packet_digest -or !$packetMeta.packet_chars){throw 'REVIEW_PACKET_INVALID'}
  $targetReviewBinding=$null
  if($TargetReceiptId){
    if($OutputMode -ne 'Envelope'){throw 'TARGET_REVIEW_MUST_NOT_APPLY_EDITS'}
    if(-not $TaskId){throw 'TARGET_REVIEW_WORK_ID_REQUIRED'}
    if($TargetReceiptId -cnotmatch '^pf:[A-Za-z0-9:_-]{8,150}$'){
      throw 'TARGET_REVIEW_RECEIPT_ID_INVALID'
    }
    $targetTool='D:\Git PWA\TAKY\TOOLS\TAKY_TARGET_REVIEW_PACKET.py'
    $targetRaw=(& python -X utf8 $targetTool --packet-file $packetFile --target-receipt $TargetReceiptId | Out-String)
    if($LASTEXITCODE -ne 0){throw 'TARGET_REVIEW_PACKET_BINDING_FAILED'}
    $targetMeta=$targetRaw|ConvertFrom-Json
    if(-not $targetMeta.target_review_binding -or -not $targetMeta.packet_digest){
      throw 'TARGET_REVIEW_PACKET_BINDING_MISSING'
    }
    $packetMeta.packet_digest=[string]$targetMeta.packet_digest
    $packetMeta.packet_chars=[int]$targetMeta.packet_chars
    $targetReviewBinding=$targetMeta.target_review_binding
  }
  $packet=Get-Content -LiteralPath $packetFile -Raw -Encoding UTF8
  $executionMode=if($Provider -eq 'codex'){'CODEX_VERIFY_ONLY'}else{'PACKET_ONLY'}
  $actionId=if($Provider -eq 'codex'){'verify:codex-packet'}else{'review:external-model'}
  if($Provider -eq 'codex'){
    # Must exactly match TAKY2.bridges CODEX_VERIFY_ONLY hardened argv.
    $argv=@($realCodex,'exec','--sandbox','read-only','--skip-git-repo-check',
      '--ephemeral','--ignore-user-config','--ignore-rules','--strict-config',
      '-c','model_reasoning_effort="medium"','-c','web_search="disabled"')
    foreach($feature in @('shell_tool','unified_exec','shell_snapshot','multi_agent',
                            'apps','hooks','remote_plugin')){$argv+=@('--disable',$feature)}
    $argv+=@('-')
  }else{
    # PACKET_ONLY: no tools, permissions, MCP, project settings or filesystem.
    $argv=@($claudeBinary,'-p','--input-format','text','--output-format','json',
      '--model','sonnet','--effort','medium','--tools','',
      '--permission-prompts','none','--no-session-persistence',
      '--strict-mcp-config','--setting-sources','','--settings','{}')
  }
  $call=@{
    model=$model; effort='medium'; context='delta'; expected_calls=1
    execution_mode=$executionMode; packet_digest=[string]$packetMeta.packet_digest
    # TAKY2 preflight signs call_digest over this bounded, source-hash manifest.
    source_manifest=@($packetMeta.included_source_files)
    skill_manifest=@($packetMeta.included_skills)
    dry_run_plan=@{
      expected_calls=1
      operations=@('one bounded packet-only review (not an independent repository investigation)')
      batch_strategy='single-review-batch'
      fallback='HOLD'
      paid_api=$false
    }
  }
  if($ScopedEditTaskSha256){
    if($OutputMode -ne 'Raw' -or !$TaskId -or
       $ScopedEditTaskSha256 -cnotmatch '^[a-f0-9]{64}$'){
      throw 'SCOPED_EDIT_CONTRACT_INVALID'
    }
    if(-not $packetMeta.included_source_files -or
       @($packetMeta.included_source_files|Where-Object {$_.complete -eq $true}).Count -lt 1){
      throw 'SCOPED_EDIT_NO_COMPLETE_SOURCE'
    }
    $call['scoped_edit_contract']=@{
      schema='TAKY_SCOPED_EDIT_CALL_V1'
      task_id=[string]$TaskId
      task_sha256=[string]$ScopedEditTaskSha256
      repo=[string]$Repo
    }
  }
  if($targetReviewBinding){
    $call['target_review_binding']=@{
      schema=[string]$targetReviewBinding.schema
      target_receipt_id=[string]$targetReviewBinding.target_receipt_id
      target_result_digest=[string]$targetReviewBinding.target_result_digest
    }
  }
  # Optional council mode: route metadata belongs inside the signed TAKY2
  # preflight CALL, not in the model's self-authored answer or local receipts.
  if ($CouncilBindingJson) {
    if (-not $TaskId) { throw 'COUNCIL_BINDING_TASK_ID_REQUIRED' }
    try {
      $rawBinding = $CouncilBindingJson | ConvertFrom-Json
      $binding = @{}
      foreach ($property in $rawBinding.PSObject.Properties) {
        $binding[$property.Name] = $property.Value
      }
    } catch { throw 'COUNCIL_BINDING_JSON_INVALID' }
    if (-not ($binding -is [hashtable]) -or
        $binding['schema'] -cne 'TAKY_COUNCIL_BINDING_V1' -or
        [string]::IsNullOrWhiteSpace([string]$binding['work_id']) -or
        [string]$binding['stage'] -cnotmatch '^(ADVISOR_|PEER_)(CONTRARIAN|FIRST_PRINCIPLES|EXPANSIONIST|OUTSIDER|EXECUTOR)$|^CHAIR$' -or
        [string]$binding['source_sha256'] -cnotmatch '^[a-f0-9]{64}$' -or
        ($null -ne $binding['target_sha256'] -and
        [string]$binding['target_sha256'] -cnotmatch '^[a-f0-9]{64}$')) {
      throw 'COUNCIL_BINDING_FIELDS_INVALID'
    }
    # Validate signed original/peer inputs against what the packet builder
    # actually read. A role-only label must not count as Council review.
    $sources = @($packetMeta.included_source_files)
    $originals = @($sources | Where-Object {
      $_.sha256 -ceq [string]$binding['source_sha256'] -and $_.complete -eq $true
    })
    if ($originals.Count -ne 1) { throw 'COUNCIL_ORIGINAL_SOURCE_NOT_INCLUDED' }
    if ([string]$binding['stage'] -like 'ADVISOR_*') {
      if ($null -ne $binding['target_sha256']) { throw 'COUNCIL_ADVISOR_TARGET_NOT_NULL' }
    } elseif ([string]$binding['stage'] -like 'PEER_*') {
      $frozen = @($sources | Where-Object {
        $_.sha256 -ceq [string]$binding['target_sha256'] -and $_.complete -eq $true
      })
      if ($frozen.Count -ne 1) { throw 'COUNCIL_PEER_FROZEN_REPORT_NOT_INCLUDED' }
    } else {
      $peerShas = @($sources | Where-Object {
        $_.sha256 -cne [string]$binding['source_sha256'] -and $_.complete -eq $true
      } | ForEach-Object { [string]$_.sha256 } | Sort-Object -CaseSensitive)
      if ($peerShas.Count -ne 5 -or @($peerShas | Sort-Object -Unique).Count -ne 5) {
        throw 'COUNCIL_CHAIR_FIVE_PEERS_NOT_INCLUDED'
      }
      $peerJson = ConvertTo-Json -InputObject $peerShas -Compress
      $peerBytes = [Text.Encoding]::UTF8.GetBytes($peerJson)
      $calculated = [BitConverter]::ToString(
        [Security.Cryptography.SHA256]::Create().ComputeHash($peerBytes)
      ).Replace('-','').ToLowerInvariant()
      if ($calculated -cne [string]$binding['target_sha256']) {
        throw 'COUNCIL_CHAIR_PEER_SET_HASH_MISMATCH'
      }
    }
    $call['council_binding'] = $binding
  }
  if($TaskId -and $TaskId -cnotmatch '^[a-f0-9]{32}$'){throw 'TASK_ID_INVALID'}
  $governedTaskId=if($TaskId){$TaskId}else{[guid]::NewGuid().ToString('N')}
  $plan=@{
    task_id='external-review-'+$governedTaskId
    action_id=$actionId
    context=@{mode='delta'}
    attempt=@{target=$Repo;method_or_tool=$routeTool}
    call=$call
  }
  $planPath=Join-Path $temp 'plan.json'
  $plan | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $planPath -Encoding UTF8
  $preErrPath=Join-Path $temp 'preflight.stderr.txt'
  # Bounded preflight: prevent an orphan PENDING receipt if the native shell pipeline stalls.
  # On timeout the supervisor releases only a strictly unclaimed receipt via TAKY2.
  $preflightTool='D:\Git PWA\TAKY\TOOLS\TAKY_PREFLIGHT_BOUNDED.py'
  # File-backed stdout prevents a stalled PowerShell Out-String pipe from leaving
  # an approved PENDING receipt before the invocation file is even created.
  $preOutPath=Join-Path $temp 'preflight.stdout.txt'
  & python -B $preflightTool $planPath 1> $preOutPath 2> $preErrPath
  $preCode=$LASTEXITCODE
  $preText=if(Test-Path -LiteralPath $preOutPath){Get-Content -LiteralPath $preOutPath -Raw}else{''}
  $preErr=if (Test-Path -LiteralPath $preErrPath) { Get-Content -LiteralPath $preErrPath -Raw } else { '' }
  if($OutputMode -ne 'Raw'){Write-Output '[TAKY_DRY_RUN_PLAN] preflight completed'}
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
  if ($ReceiptOut) {
    @{task_id=$governedTaskId;receipt_id=$pre.receipt_id;provider=$Provider;
      executor_state='AUTHORIZED_NOT_YET_CONFIRMED_INVOKED';
      packet_digest=[string]$packetMeta.packet_digest;
      source_manifest=@($packetMeta.included_source_files);
      skill_manifest=@($packetMeta.included_skills);call_manifest=$call} |
      ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReceiptOut -Encoding UTF8
  }

  # PowerShell 5.1 ConvertTo-Json can consume unbounded CPU/RAM when
  # serializing a 40K stdin string with a nested signed call manifest.
  # Use the existing Python packet helper; it preserves the exact signed
  # call, verifies packet digest, and round-trips invocation JSON.
  $argvPath=Join-Path $temp 'invocation.argv.txt'
  [IO.File]::WriteAllLines($argvPath,[string[]]$argv,[Text.UTF8Encoding]::new($false))
  $invPath=Join-Path $temp 'invocation.json'
  $serializedRaw=(& python -X utf8 $packetTool --invocation-plan $planPath --packet-file $packetFile `
    --invocation-argv $argvPath --invocation-out $invPath `
    --invocation-provider $providerName --invocation-tool $routeTool | Out-String)
  if($LASTEXITCODE -ne 0){throw 'SIGNED_INVOCATION_JSON_SERIALIZATION_FAILED'}
  $serialized=$serializedRaw|ConvertFrom-Json
  if($serialized.invocation_serialized -ne $true -or
     [string]$serialized.packet_digest -cne [string]$packetMeta.packet_digest){
    throw 'SIGNED_INVOCATION_SERIALIZATION_READBACK_HOLD'
  }
  $execErrPath=Join-Path $temp 'execute.stderr.txt'
  $execOutPath=Join-Path $temp 'execute.stdout.txt'
  & python -B -m TAKY2.orchestrator execute $pre.receipt_id $invPath --executor-id ('TAKY_MODEL_REVIEW_'+$Provider.ToUpper()) 1> $execOutPath 2> $execErrPath
  $execCode=$LASTEXITCODE
  $execText=if(Test-Path -LiteralPath $execOutPath){Get-Content -LiteralPath $execOutPath -Raw}else{''}
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
    @{task_id=$governedTaskId;receipt_id=$pre.receipt_id; provider=$Provider; executor_state=$exec.state;
      packet_digest=[string]$packetMeta.packet_digest;
      source_manifest=@($packetMeta.included_source_files);
      skill_manifest=@($packetMeta.included_skills);call_manifest=$call} |
      ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReceiptOut -Encoding UTF8
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
