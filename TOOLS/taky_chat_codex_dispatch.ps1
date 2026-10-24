param(
 [Parameter(Mandatory=$true)][string]$TaskFile,
 [switch]$Execute
)
$ErrorActionPreference='Stop'
$task=Get-Content -LiteralPath $TaskFile -Raw -Encoding UTF8 | ConvertFrom-Json
if($task.schema -ne 'TAKY_EXECUTION_REQUEST_V1' -or $task.executor -ne 'Codex'){throw 'WRONG_TASK'}
if($task.state -ne 'PREPARED_NOT_EXECUTED'){throw 'INVALID_STATE'}
# Direct Codex dispatch must obey the same exact Workbench binding gate as
# orchestrated dispatch. Legacy unbound requests are historical HOLD, not work.
if([string]::IsNullOrWhiteSpace([string]$task.portfolio_task_id)){
 throw 'PORTFOLIO_WORK_ID_REQUIRED_FOR_MODEL_TASK'
}
$portfolio=Get-Content -LiteralPath 'D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\70_EXECUTION_QUEUE\TASK_REGISTER.json' -Raw -Encoding UTF8|ConvertFrom-Json
$matching=@($portfolio.tasks|Where-Object {[string]$_.id -ceq [string]$task.portfolio_task_id})
if($matching.Count -ne 1){throw 'PORTFOLIO_ID_NOT_FOUND_OR_DUPLICATE'}
if($matching[0].status -in @('BLOCKED','REJECTED','VERIFIED')){throw 'PORTFOLIO_TASK_NOT_ACTIVE'}
if($matching[0].approval_required -eq $true){throw 'PORTFOLIO_NEEDS_SEPARATE_APPROVAL'}
# Rebind at actual dispatch; a prepared ID alone is not ownership proof.
$registry=Get-Content -LiteralPath 'D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL\PROJECT_REGISTRY.json' -Raw -Encoding UTF8|ConvertFrom-Json
$ownerRepo=if($task.repo -eq 'D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH'){'D:\Git PWA\TAKY'}else{[string]$task.repo}
$projects=@($registry.projects.PSObject.Properties|Where-Object {
 [string]::Equals([IO.Path]::GetFullPath(([string]$_.Value.source_repo).Replace('/','\')),[IO.Path]::GetFullPath($ownerRepo),[StringComparison]::OrdinalIgnoreCase)
})
if($projects.Count -ne 1){throw 'PORTFOLIO_REPO_OWNER_NOT_REGISTERED'}
$currentWork=Get-Content -LiteralPath ('D:\Git PWA\TAKY_AI_WORKBENCH\10_PROJECTS\'+$projects[0].Name+'\PROJECT_CURRENT.json') -Raw -Encoding UTF8|ConvertFrom-Json
if($currentWork.status -eq 'IDLE' -or $registry.projects.($projects[0].Name).status -ne $currentWork.status){throw 'PORTFOLIO_WORK_ID_REPO_SCOPE_MISMATCH'}
# Allow a parallel active WORK_ID only with its own in-repo evidence, never
# by borrowing the primary CURRENT task's sources.
$primary=([string]$currentWork.current_work_id -ceq [string]$task.portfolio_task_id)
$repoPrefix=[IO.Path]::GetFullPath([string]$task.repo).TrimEnd('\')+'\'
$workRefs=@($matching[0].evidence|Where-Object {$_ -is [string] -and $_.StartsWith($repoPrefix,[StringComparison]::OrdinalIgnoreCase)})
if(!$primary -and $workRefs.Count -eq 0){throw 'PORTFOLIO_WORK_ID_REPO_SCOPE_MISMATCH'}
$refs=if($primary){@($matching[0].evidence)+@($currentWork.source_refs)+@($currentWork.output_refs)}else{@($workRefs)}
$pattern='(?<![A-Za-z0-9_.-])((?:TAKY2|TOOLS|ENFORCEMENT|DOMAIN|LEARNING|src|app|lib|pages|components|tests)/[A-Za-z0-9_./-]+\.(?:ps1|py|js|cjs|mjs|ts|tsx|jsx|json|css|html|md))\b'
$named=@([regex]::Matches([string]$task.task,$pattern,[Text.RegularExpressions.RegexOptions]::IgnoreCase)|ForEach-Object {$_.Groups[1].Value}|Sort-Object -Unique)
if($named.Count -eq 0 -and $task.task_kind -ne 'implementation'){throw 'PORTFOLIO_TASK_SOURCE_REF_REQUIRED'}
foreach($rel in $named){
 if($rel.Contains('..')){throw 'PORTFOLIO_TASK_SOURCE_PATH_INVALID'}
 $target=[IO.Path]::GetFullPath((Join-Path ([string]$task.repo) ($rel.Replace('/','\'))))
 $hits=@($refs|Where-Object {$_ -and [string]::Equals([IO.Path]::GetFullPath([string]$_),$target,[StringComparison]::OrdinalIgnoreCase)})
 if($hits.Count -eq 0){throw ('PORTFOLIO_TASK_SOURCE_NOT_OWNED: '+$rel)}
}
$allow=@('D:\Git PWA\TAKY','D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH','D:\Git PWA\Play Camp','D:\Git PWA\Ready & Set','D:\Git PWA\Hide & Seek','D:\Git PWA\Snap & Pop','D:\Git PWA\TAKY-MOBILE','D:\Git PWA\SAVEY')
if($task.repo -notin $allow){throw 'REPO_NOT_ALLOWED'}
if($task.task_kind -eq 'implementation'){
 $fileScope=@($task.allowed_files|Where-Object {$_})
 if($fileScope.Count -eq 0){throw 'PORTFOLIO_EDIT_FILES_REQUIRED'}
 foreach($entry in $fileScope){
  $rel=[string]$entry.path
  if($rel -notmatch '^[A-Za-z0-9_./-]+$' -or $rel.Contains('..') -or $rel.StartsWith('/')){throw 'PORTFOLIO_EDIT_PATH_INVALID'}
  $file=Join-Path ([string]$task.repo) ($rel.Replace('/','\'))
  if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw 'PORTFOLIO_EDIT_FILE_MISSING'}
  $target=[IO.Path]::GetFullPath($file)
  $owned=@($refs|Where-Object {$_ -and [string]::Equals([IO.Path]::GetFullPath([string]$_),$target,[StringComparison]::OrdinalIgnoreCase)})
  if($owned.Count -eq 0){throw ('PORTFOLIO_EDIT_SOURCE_NOT_OWNED: '+$rel)}
  if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -cne [string]$entry.sha256){throw 'PORTFOLIO_EDIT_FILE_CHANGED_REPREPARE'}
 }
}elseif(@($task.allowed_files|Where-Object {$_}).Count -gt 0){throw 'PORTFOLIO_REVIEW_WITH_EDIT_FILES'}
if(!(Test-Path -LiteralPath $task.repo)){throw 'MISSING_REPO'}
$current=(git -C $task.repo rev-parse HEAD)
if($LASTEXITCODE -ne 0 -or $current -ne $task.head){throw 'HEAD_CHANGED_REPREPARE'}
# The task-preparation snapshot is evidence, not a permanent quota authorization.
# Recheck before dispatch; never spend a model call on a stale/unsafe balance.
$kind=if($task.task_kind){[string]$task.task_kind}else{'code'}
$size=if($task.task_size){[string]$task.task_size}else{'medium'}
$count=if($task.planned_calls){[int]$task.planned_calls}else{1}
$usageScript='D:\Git PWA\TAKY\TOOLS\TAKY_USAGE_BOARD.py'
$raw=(& python -X utf8 $usageScript --route-dry-run --task-kind $kind --task-size $size --planned-calls $count | Out-String)
if($LASTEXITCODE -ne 0){throw 'USAGE_PREFLIGHT_UNAVAILABLE'}
try{$route=$raw | ConvertFrom-Json}catch{throw 'USAGE_PREFLIGHT_INVALID'}
$codex=@($route.candidates | Where-Object {$_.provider -eq 'Codex CLI' -and $_.risk -eq 'SAFE'})
if($route.status -ne 'READY_FOR_SEPARATE_AUTHORIZATION' -or $codex.Count -ne 1){
 throw ('USAGE_ROUTE_HOLD_REPREPARE: '+[string]$route.status)
}
if($task.route_selection -eq 'AUTO' -and $route.recommended -ne 'Codex CLI'){
 throw 'USAGE_ROUTE_CHANGED_REPREPARE'
}
# The signed TAKY2 route must be open, not merely within quota.
$healthScript='D:\Git PWA\TAKY\TOOLS\TAKY_GOVERNED_ROUTE_HEALTH.py'
$healthRaw=(& python -X utf8 $healthScript --executor Codex --repo ([string]$task.repo) | Out-String)
if($LASTEXITCODE -ne 0){throw 'GOVERNED_ROUTE_HEALTH_UNAVAILABLE'}
try{$health=$healthRaw|ConvertFrom-Json}catch{throw 'GOVERNED_ROUTE_HEALTH_INVALID'}
if($health.status -ne 'READY_FOR_EXISTING_COST_AND_APPROVAL_GATES'){
 throw ('TAKY_GOVERNANCE_ROUTE_HOLD: '+[string]$health.reason)
}
if(!$Execute){
 @{status='READY_NO_MODEL_CALL';executor='Codex';usagePreflight=$route
   modelCalled=$false} | ConvertTo-Json -Depth 12
 exit 0
}
if($env:TAKY_USER_EXPLICIT_AUTHORIZATION -ne '1'){throw 'EXPLICIT_AUTHORIZATION_REQUIRED'}
$governed='D:\Git PWA\TAKY\TOOLS\TAKY_MODEL_REVIEW.ps1'
$real='C:\Users\YKH_1507-03\AppData\Roaming\npm\codex.cmd'
if(!(Test-Path -LiteralPath $governed) -or !(Test-Path -LiteralPath $real)){throw 'CODEX_INSTALL_MISSING'}
$receiptDir='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY'
$receipt=Join-Path $receiptDir ("CODEX_CHAT_"+$task.id+".json")
$env:TAKY_USER_INTENT=[string]$task.task
# Subscription route only: never allow API key environment fallback.
foreach($key in @('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY')){
 Remove-Item ("Env:"+$key) -ErrorAction SilentlyContinue
}
$details=[ordered]@{
 id=$task.id;executor='Codex';status='STARTED'
 created_utc=[DateTime]::UtcNow.ToString('o');repo=$task.repo
 result='';exit_code=$null
 governed_transport='TAKY2_MODEL_REVIEW_CODEX_STDIN_DEVNULL'
 quota_before=$codex[0].beforeUsedPercent
 quota_before_observed_at=$codex[0].observedAt
 quota_after=$null;quota_after_observed_at=$null
 calibration_status='NOT_MEASURABLE_UNTIL_FRESH_QUOTA'
}
try {
 Push-Location $task.repo
 # Avoid a piped CLI stdin. TAKY2 bridge closes stdin and bounds time.
 # The governed wrapper handles Codex subscription auth and fresh receipt checks.
 $output=(& $governed -Provider codex -Prompt ([string]$task.task) -Repo ([string]$task.repo) 2>&1 | Out-String)
 $exitCode=$LASTEXITCODE
 $details.result=$output.Substring(0,[Math]::Min($output.Length,20000))
 $details.exit_code=$exitCode
 $details.status=if($exitCode -eq 0){'COMPLETE_UNVERIFIED'}else{'FAILED'}
} catch { $details.status='ERROR';$details.result=$_.Exception.Message }
finally {
 Pop-Location
 # Read only the last available quota, which may be cached for 30 minutes.
 # Never claim that a quota change was caused solely by this run.
 try {
  $afterRaw=(& python -X utf8 $usageScript --route-dry-run --task-kind $kind --task-size $size --planned-calls $count | Out-String)
  if($LASTEXITCODE -eq 0){
   $after=$afterRaw | ConvertFrom-Json
   $afterCodex=@($after.candidates | Where-Object {$_.provider -eq 'Codex CLI'})
   if($afterCodex.Count -eq 1){
    $details.quota_after=$afterCodex[0].beforeUsedPercent
    $details.quota_after_observed_at=$afterCodex[0].observedAt
    if($details.quota_before_observed_at -ne $details.quota_after_observed_at){
     $details.calibration_status='OBSERVED_DIFFERENCE_NOT_TASK_ATTRIBUTED'
    }
   }
  }
 } catch {$details.calibration_status='AFTER_SNAPSHOT_UNAVAILABLE'}
 $details.finished_utc=[DateTime]::UtcNow.ToString('o')
 [IO.Directory]::CreateDirectory($receiptDir)|Out-Null
 [IO.File]::WriteAllText($receipt,($details|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
}
$details|ConvertTo-Json -Depth 6
