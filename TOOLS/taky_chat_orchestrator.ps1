param(
 [ValidateSet('Status','Intake','GitStatus','LocalRepoInfo','LocalVerify','RouteDryRun','AdvanceLocal','ContinueLocal','Dispatch','RunPrepared','ApplyScopedEdit')][string]$Action='Status',
 [string]$Repo='D:\Git PWA\TAKY',
 [ValidateSet('Auto','Claude','Codex')][string]$Executor='Auto',
 [ValidateSet('code','implementation','review','validation')][string]$TaskKind='code',
 [ValidateSet('small','medium','large')][string]$TaskSize='medium',
 [ValidateRange(1,4)][int]$PlannedCalls=1,
 [string]$Task='',
 [string[]]$AllowedFiles=@(),
 [string]$AcceptanceCriteria='',
 [string]$PortfolioTaskId='',
 [string]$Project='',
 [string]$Category='INTEGRATION',
 [string]$Priority='P1',
 [string]$ParentWorkId='',
 [string]$RequestKey='',
 [string[]]$SourcePaths=@(),
 [switch]$DryRunIntake,
 [string]$TaskFile='',
 [string]$ProposalFile='',
 [switch]$AuthorizeFileApply,
 [switch]$AuthorizeModelCall
)
$ErrorActionPreference='Stop'
# Load the trusted Windows PowerShell module explicitly on hosts without
# module autoloading; Get-FileHash is exported as a Function on PowerShell 5.1.
$utilityModule='C:\Windows\System32\WindowsPowerShell\v1.0\Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1'
Import-Module -Name $utilityModule -ErrorAction Stop
$hashCommand=Get-Command Get-FileHash -ErrorAction SilentlyContinue
if (-not $hashCommand -or $hashCommand.Source -cne 'Microsoft.PowerShell.Utility') {
 throw 'POWERSHELL_SHA256_COMMAND_UNTRUSTED_OR_UNAVAILABLE'
}
$repos=@('D:\Git PWA\TAKY','D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH','D:\Git PWA\Play Camp','D:\Git PWA\Ready & Set','D:\Git PWA\Hide & Seek','D:\Git PWA\Snap & Pop','D:\Git PWA\TAKY-MOBILE','D:\Git PWA\SAVEY')
if($Repo -notin $repos){throw 'Repository not allowlisted'}
if(!(Test-Path -LiteralPath $Repo)){throw 'Repository path unavailable'}
$root='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON'
$history=Join-Path $root '04_HISTORY'
if($Action -notin @('Intake','RouteDryRun','Status','AdvanceLocal','ContinueLocal')){[System.IO.Directory]::CreateDirectory($history)|Out-Null}
$id=[guid]::NewGuid().ToString('N')
$start=[DateTime]::UtcNow.ToString('o')
$result=[ordered]@{schema='TAKY_CHAT_ORCH_V1';id=$id;action=$Action;repo=$Repo;executor=$null;started_utc=$start;status='STARTED';model_called=$false;output=''}
function Sync-WorkbenchAssignment($taskId,$taskFile,$executor,$taskRepo,[string]$evidenceFile='') {
 if($taskId -notmatch '^[0-9a-f]{32}$' -or $executor -notin @('Claude','Codex')){throw 'INVALID_WORK_ID'}
 $key='TAKY-CHAT-'+$taskId
 $registry='D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL\AI_WORK_ASSIGNMENTS.json'
 $guard=[Threading.Mutex]::new($false,'Local\TAKY_WORK_ASSIGNMENT_MUTEX')
 $owned=$false
 try {
  $owned=$guard.WaitOne(5000)
  if(!$owned){throw 'ASSIGNMENT_LOCK_BUSY'}
  $task=Get-Content -LiteralPath $taskFile -Raw -Encoding UTF8|ConvertFrom-Json
  if($task.id -cne $taskId -or $task.repo -cne $taskRepo -or $task.executor -cne $executor -or $task.state -ne 'PREPARED_NOT_EXECUTED'){throw 'TASK_BINDING_MISMATCH'}
  # Legacy prepared tasks without an explicit existing portfolio ID stay
  # readable as history, but cannot create new unowned model work.
  if([string]::IsNullOrWhiteSpace([string]$task.portfolio_task_id)){
   throw 'PORTFOLIO_WORK_ID_REQUIRED_FOR_MODEL_TASK'
  }
  $doc=Get-Content -LiteralPath $registry -Raw -Encoding UTF8|ConvertFrom-Json
  if($doc.schema -ne 'TAKY_AI_WORK_ASSIGNMENTS_V1' -or $null -eq $doc.tasks){throw 'REGISTRY_SCHEMA_MISMATCH'}
  $inputs=@($taskFile)
  $eventIds=@([regex]::Matches([string]$task.task,'REV-[0-9a-f]{24}')|ForEach-Object {$_.Value}|Select-Object -Unique)
  foreach($eventId in $eventIds){
   $eventPath=Join-Path 'D:\Git PWA\TAKY-SOURCE-VAULT\data\direction_intake\review_events' ($eventId+'.json')
   $event=Get-Content -LiteralPath $eventPath -Raw -Encoding UTF8|ConvertFrom-Json
   if($event.event_id -cne $eventId -or [string]$event.event_hash -notmatch '^[0-9a-f]{64}$' -or
      $event.event_hash.Substring(0,24) -cne $eventId.Substring(4)){throw 'REVIEW_EVENT_BINDING_INVALID'}
   $inputs+= $eventPath
  }
  if([string]$task.portfolio_task_id){
   $portfolio=Get-Content -LiteralPath 'D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\70_EXECUTION_QUEUE\TASK_REGISTER.json' -Raw -Encoding UTF8|ConvertFrom-Json
   $portfolioMatches=@($portfolio.tasks|Where-Object {[string]$_.id -ceq [string]$task.portfolio_task_id})
   if($portfolioMatches.Count -ne 1){throw 'PORTFOLIO_TASK_BINDING_LOST'}
   if($portfolioMatches[0].status -in @('BLOCKED','REJECTED','VERIFIED')){throw 'PORTFOLIO_TASK_NOT_ACTIVE'}
   if($portfolioMatches[0].approval_required -eq $true){throw 'PORTFOLIO_NEEDS_SEPARATE_APPROVAL'}
  }
  $match=@($doc.tasks|Where-Object {$_.work_id -eq $key})
  if($match.Count -gt 1){throw 'DUPLICATE_WORK_ID'}
  if($match.Count -eq 1){
   if($match[0].project -cne $taskRepo -or @($inputs|Where-Object {@($match[0].input_refs) -notcontains $_}).Count -gt 0 -or
      [string]$match[0].portfolio_task_id -cne [string]$task.portfolio_task_id){throw 'WORK_ID_CONFLICT'}
   if(!$evidenceFile -or @($match[0].evidence_refs) -contains $evidenceFile){return $key}
   if(!(Test-Path -LiteralPath $evidenceFile -PathType Leaf)){throw 'EVIDENCE_RECEIPT_MISSING'}
   $proof=Get-Content -LiteralPath $evidenceFile -Raw -Encoding UTF8|ConvertFrom-Json
   if($proof.schema -ne 'TAKY_CHAT_ORCH_V1' -or $proof.work_id -cne $key -or $proof.task_id -cne $taskId){throw 'EVIDENCE_TASK_MISMATCH'}
   $match[0].evidence_refs=@($match[0].evidence_refs)+@($evidenceFile)
   if($proof.status -in @('HOLD','FAILED','OUTCOME_UNKNOWN','PROPOSAL_REJECTED')){$match[0].status='BLOCKED'}
   if($proof.status -in @('COMPLETE_UNVERIFIED','PROPOSAL_VALIDATED_NOT_APPLIED','APPLIED_UNVERIFIED')){$match[0].status='REVIEW'}
   if($proof.execution_receipt -and @($match[0].output_refs) -notcontains [string]$proof.execution_receipt -and
      (Test-Path -LiteralPath ([string]$proof.execution_receipt) -PathType Leaf)){
    $match[0].output_refs=@($match[0].output_refs)+@([string]$proof.execution_receipt)
   }
  }else{
   $record=[ordered]@{work_id=$key;project=$taskRepo;portfolio_task_id=[string]$task.portfolio_task_id;owner='TAKY_ORCHESTRATOR';reviewer='UNASSIGNED';authority_ref='D:/Git PWA/TAKY/CURRENT';input_refs=@($inputs);output_refs=@();status='OPEN';evidence_refs=@();executor=$executor;task_id=$taskId;execution_verified=$false}
   $doc.tasks=@($doc.tasks)+@($record)
  }
  $before=(Get-FileHash -LiteralPath $registry -Algorithm SHA256).Hash
  if((Get-FileHash -LiteralPath $registry -Algorithm SHA256).Hash -ne $before){throw 'REGISTRY_CHANGED'}
  $tmp=$registry+'.tmp.'+[guid]::NewGuid().ToString('N')
  try{
   [IO.File]::WriteAllText($tmp,($doc|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
   Move-Item -LiteralPath $tmp -Destination $registry -Force -ErrorAction Stop
  }finally{if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force}}
  $readback=Get-Content -LiteralPath $registry -Raw -Encoding UTF8|ConvertFrom-Json
  if(@($readback.tasks|Where-Object {$_.work_id -eq $key}).Count -ne 1){throw 'REGISTRY_READBACK_FAILED'}
  return $key
 }finally{if($owned){$guard.ReleaseMutex()|Out-Null};$guard.Dispose()}
}
try {
 switch($Action){
  'Intake' {
   # Portfolio task identity precedes source verification and implementation.
   if(!$Project -or !$Task){throw 'WORK_INTAKE_PROJECT_AND_TITLE_REQUIRED'}
   $router='D:\Git PWA\TAKY\TOOLS\setup_workbench_backlog.py'
   $intakeArgs=@($router,'--intake','--project',$Project,'--title',$Task,
                 '--category',$Category,'--priority',$Priority)
   if($PortfolioTaskId){$intakeArgs+=@('--existing-id',$PortfolioTaskId)}
   if($ParentWorkId){$intakeArgs+=@('--parent-work-id',$ParentWorkId)}
   if($RequestKey){$intakeArgs+=@('--request-key',$RequestKey)}
   foreach($p in $SourcePaths){$intakeArgs+=@('--source',$p)}
   if($DryRunIntake){$intakeArgs+='--dry-run'}
   $raw=(& python -B -X utf8 @intakeArgs | Out-String)
   if($LASTEXITCODE -ne 0){throw 'WORK_INTAKE_REGISTER_HOLD'}
   try{$assigned=$raw|ConvertFrom-Json}catch{throw 'WORK_INTAKE_READBACK_INVALID'}
   if($assigned.status -notin @('WORK_ID_ASSIGNED_AT_INTAKE','EXISTING_WORK_ID_REUSED') -or
      $assigned.model_called -ne $false -or $assigned.done_issued -ne $false -or
      [string]$assigned.work_id -notmatch '^[A-Za-z0-9-]{3,64}$'){
    throw 'WORK_INTAKE_BOUNDARY_INVALID'
   }
   $result['work_id']=[string]$assigned.work_id
   $result['portfolio_task_id']=[string]$assigned.work_id
   $result['project']=[string]$assigned.classified_project
   $result['parent_work_id']=$assigned.parent_work_id
   $result['task_state']=[string]$assigned.task_state
   $result['source_bindings']=[int]$assigned.planned_source_bindings
   $result['dry_run']=[bool]$assigned.dry_run
   $result.status=[string]$assigned.status
   $result.output='WORK_ID_BOUND_BEFORE_IMPLEMENTATION; ZERO_MODEL_CALLS; NOT_DONE'
  }
  'Status' {
   $observer='D:\Git PWA\TAKY\TOOLS\TAKY_ORCHESTRATION_RECONCILE.py'
   $snapshotRaw=(& python -B -X utf8 $observer | Out-String)
   if($LASTEXITCODE -ne 0){throw 'ORCHESTRATION_RECONCILIATION_UNAVAILABLE'}
   $snapshot=$snapshotRaw|ConvertFrom-Json
   if($snapshot.schema -ne 'TAKY_ORCHESTRATION_RECONCILIATION_V1' -or
      $snapshot.model_calls_made_by_reconciliation -ne 0){throw 'ORCHESTRATION_RECONCILIATION_INVALID'}
   $localPlanRaw=(& python -B -X utf8 'D:\Git PWA\TAKY\TOOLS\TAKY_ORCHESTRATION_ADVANCE.py' | Out-String)
   if($LASTEXITCODE -ne 0){throw 'LOCAL_WORK_PLAN_UNAVAILABLE'}
   $localPlan=$localPlanRaw|ConvertFrom-Json
   if($localPlan.schema -ne 'TAKY_LOCAL_NEXT_WORK_V1' -or $localPlan.no_model_calls -ne $true){throw 'LOCAL_WORK_PLAN_INVALID'}
   $localEvidence=@($localPlan.considered|Where-Object {$_.route -eq 'LOCAL_SLICE_ALREADY_EVIDENCED'})
   $result['work_snapshot']=$snapshot
   $result['local_work']=[ordered]@{
     evidenced_slices=$localEvidence.Count
     evidenced_task_ids=@($localEvidence|ForEach-Object {[string]$_.task_id})
     next_ready_task_id=if($localPlan.selected){[string]$localPlan.selected.task_id}else{$null}
     eligible_now=[int]$localPlan.eligible_count
     scope='LOCAL_DIAGNOSTIC_SLICES_ONLY_NOT_PORTFOLIO_COMPLETION'
   }
   $result.status='ORCHESTRATION_REVIEW_REQUIRED'
   $result.output="Portfolio $($snapshot.portfolio.total) tasks, AI jobs $($snapshot.model_jobs.total), independently verified model jobs $($snapshot.model_jobs.verified_by_registry), local slices evidenced $($localEvidence.Count), locally ready $($localPlan.eligible_count). Independent completion review still required."
  }
  'AdvanceLocal' {
   $localWorker='D:\Git PWA\TAKY\TOOLS\TAKY_ORCHESTRATION_ADVANCE.py'
   $proofRaw=(& python -B -X utf8 $localWorker --perform | Out-String)
   if($LASTEXITCODE -ne 0){throw 'LOCAL_ADVANCE_EXECUTOR_FAILED'}
   $proof=$proofRaw|ConvertFrom-Json
   if($proof.no_model_calls -ne $true -or
      $proof.status -notin @('LOCAL_SLICE_VERIFIED_NOT_PORTFOLIO_DONE','LOCAL_SLICE_FINDINGS_NEED_ACTION',
                             'NO_APPROVED_LOCAL_WORK_READY')){throw 'LOCAL_ADVANCE_PROOF_INVALID'}
   $result['local_work_proof']=$proof
   $result.status=[string]$proof.status
   $result.output=if($proof.task_id){"Local task $($proof.task_id): $($proof.status); portfolio completion remains separate."}else{"No unverified approved local execution slice. Do not repeat existing proof."}
  }
  'ContinueLocal' {
   $localWorker='D:\Git PWA\TAKY\TOOLS\TAKY_ORCHESTRATION_ADVANCE.py'
   $batchRaw=(& python -B -X utf8 $localWorker --continue | Out-String)
   if($LASTEXITCODE -ne 0){throw 'LOCAL_CONTINUATION_WORKER_FAILED'}
   $batch=$batchRaw|ConvertFrom-Json
   if($batch.schema -ne 'TAKY_LOCAL_CONTINUATION_V1' -or
      $batch.no_model_calls -ne $true -or
      $batch.portfolio_done_claimed -ne $false -or
      $batch.no_push_merge_deploy -ne $true){throw 'LOCAL_CONTINUATION_PROOF_INVALID'}
   $result['continuation']=$batch
   $result.status=[string]$batch.status
   $result.output="Executed $(@($batch.actions).Count) available local tasks in one request, with per-task proof and no additional user confirmations. Full portfolio completion is NOT asserted."
  }
  'GitStatus' {
   $result.output=((git -C $Repo status --short 2>&1 | Select-Object -First 80) -join "`n")
   if($LASTEXITCODE -ne 0){throw "git status failed"}
  }
  'LocalRepoInfo' {
   $head=(git -C $Repo rev-parse --short HEAD)
   if($LASTEXITCODE -ne 0){throw 'git HEAD failed'}
   $branch=(git -C $Repo branch --show-current)
   $remote=(git -C $Repo remote get-url origin 2>$null)
   $result.output="HEAD=$head; BRANCH=$branch; REMOTE_CONFIG=$remote (local config only)"
  }
  'LocalVerify' {
   $tracked=@(git -C $Repo diff --name-only --diff-filter=ACMR)
   if($LASTEXITCODE -ne 0){throw 'local changed-file list failed'}
   $check= @(git -C $Repo diff --check 2>&1)
   $diffExit=$LASTEXITCODE
   $scripts=@(Get-ChildItem -LiteralPath (Join-Path $Repo 'TOOLS') -Filter 'taky_*bridge*.ps1' -File -ErrorAction SilentlyContinue)
   $parseErrors=@()
   foreach($f in $scripts){
    $tok=$null;$err=$null
    [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName,[ref]$tok,[ref]$err)
    if($err){$parseErrors+=@($err | ForEach-Object {"$($f.Name): $($_.Message)"})}
   }
   if($diffExit -ne 0 -or $parseErrors.Count -gt 0){throw "VERIFY_FAILED: diff=$diffExit parse=$($parseErrors -join '; ')"}
   $result.output="LOCAL_VERIFY_PASS: tracked_changes=$($tracked.Count) diff_check=0 parse_checked=$($scripts.Count) parse_errors=0"
  }
  'RouteDryRun' {
   if([string]::IsNullOrWhiteSpace($Task)){throw 'Task required'}
   $prepare='D:\Git PWA\TAKY\TOOLS\taky_chat_task_prepare.ps1'
   if($TaskKind -eq 'review'){
     if($AllowedFiles.Count -ne 0){throw 'REVIEW_CANNOT_EDIT'}
     $raw=(& $prepare -Task $Task -Executor $Executor -TaskKind $TaskKind -TaskSize $TaskSize -PlannedCalls $PlannedCalls -Repo $Repo -PortfolioTaskId $PortfolioTaskId -DryRun | Out-String)
   }else{
     $raw=(& $prepare -Task $Task -Executor $Executor -TaskKind $TaskKind -TaskSize $TaskSize -PlannedCalls $PlannedCalls -Repo $Repo -AllowedFiles $AllowedFiles -AcceptanceCriteria $AcceptanceCriteria -PortfolioTaskId $PortfolioTaskId -DryRun | Out-String)
   }
   if($LASTEXITCODE -ne 0){throw 'ROUTE_PREP_FAILED'}
   $route=$raw|ConvertFrom-Json
   if($route.status -ne 'READY_FOR_SEPARATE_AUTHORIZATION' -and $route.status -ne 'LOCAL_ONLY_NO_MODEL_TASK'){throw 'USAGE_GATE_HOLD'}
   $result.executor=$route.selectedExecutor
   $result['route']=$route.route
   $result['portfolio_task_id']=[string]$route.portfolioTaskId
   $result.status='DRYRUN_READY'
   $result.output='Zero model calls; no new task prepared'
  }
  'ApplyScopedEdit' {
   if(!$TaskFile -or !$ProposalFile){throw 'EDIT_TASK_AND_PROPOSAL_REQUIRED'}
   $inbox=Join-Path $root '01_INBOX\AI_TASKS'
   $taskPath=[IO.Path]::GetFullPath($TaskFile)
   if(!$taskPath.StartsWith(([IO.Path]::GetFullPath($inbox).TrimEnd('\')+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'TASK_FILE_OUTSIDE_APPROVED_INBOX'}
   $job=Get-Content -LiteralPath $taskPath -Raw -Encoding UTF8|ConvertFrom-Json
   if($job.mode -ne 'BOUNDED_EDIT_PROPOSAL' -or $job.state -ne 'PREPARED_NOT_EXECUTED'){throw 'NOT_AN_EDIT_TASK'}
   $runner='D:\Git PWA\TAKY\TOOLS\TAKY_SCOPED_EDIT_APPLY.py'
   $argsList=@($runner,'--task-file',$taskPath,'--proposal-file',$ProposalFile)
   if($AuthorizeFileApply){
    if($env:TAKY_USER_EXPLICIT_AUTHORIZATION -ne '1' -or $env:TAKY_ALLOW_SCOPED_FILE_EDIT -ne '1'){throw 'SCOPED_EDIT_AUTHORIZATION_REQUIRED'}
    $prior=Join-Path $history ('TAKY_ROUTED_'+$job.id+'.json')
    if(!(Test-Path -LiteralPath $prior -PathType Leaf)){throw 'SCOPED_EDIT_SIGNED_EXECUTION_NOT_FOUND'}
    $proof=Get-Content -LiteralPath $prior -Raw -Encoding UTF8|ConvertFrom-Json
    if([string]$proof.task_id -cne [string]$job.id -or
       [string]$proof.proposal_file -cne [string]$ProposalFile -or
       !$proof.taky2_signed_receipt_id){throw 'SCOPED_EDIT_EXECUTION_EVIDENCE_MISMATCH'}
    $argsList+= @('--apply','--signed-receipt',([string]$proof.taky2_signed_receipt_id),
                  '--execution-record',$prior)
   }
   $raw=(& python -X utf8 @argsList | Out-String)
   $parsed=$raw|ConvertFrom-Json
   $result.status=[string]$parsed.status
   $result['files']=$parsed.files
   $result['task_id']=$parsed.task_id
   $result.output=if($parsed.reason){[string]$parsed.reason}else{'Hash-bound scoped edit validation completed'}
  }
  'RunPrepared' {
   if(!$TaskFile -or !(Test-Path -LiteralPath $TaskFile -PathType Leaf)){throw 'TASK_FILE_REQUIRED'}
   $inbox=Join-Path $root '01_INBOX\AI_TASKS'
   $resolved=[IO.Path]::GetFullPath($TaskFile)
   $prefix=[IO.Path]::GetFullPath($inbox).TrimEnd('\')+'\'
   if(!$resolved.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'TASK_FILE_OUTSIDE_APPROVED_INBOX'}
   $job=Get-Content -LiteralPath $resolved -Raw -Encoding UTF8|ConvertFrom-Json
   if($job.schema -ne 'TAKY_EXECUTION_REQUEST_V1' -or $job.state -ne 'PREPARED_NOT_EXECUTED' -or
      $job.mode -notin @('READ_ONLY_REVIEW','BOUNDED_EDIT_PROPOSAL') -or $job.approval -ne 'REQUIRED_BEFORE_MODEL_CALL' -or
      $job.no_push -ne $true -or $job.no_deploy -ne $true){throw 'UNSAFE_OR_INVALID_TASK'}
   if($job.id -notmatch '^[0-9a-f]{32}$' -or $job.repo -notin $repos -or
      $job.route_selection -notin @('AUTO','EXPLICIT') -or
      $job.task_kind -notin @('code','review','implementation') -or
      $job.task_size -notin @('small','medium','large') -or
      [int]$job.planned_calls -lt 1 -or [int]$job.planned_calls -gt 4 -or
      [string]::IsNullOrWhiteSpace([string]$job.task) -or
      ([string]$job.task).Length -gt 2500){throw 'TASK_CONTRACT_INVALID'}
   if($job.task_kind -eq 'implementation'){
    if($job.mode -ne 'BOUNDED_EDIT_PROPOSAL' -or !$job.acceptance_criteria -or
       @($job.allowed_files).Count -lt 1){throw 'IMPLEMENTATION_SCOPE_NOT_BOUND'}
    foreach($item in $job.allowed_files){
     $check=Join-Path ([string]$job.repo) (([string]$item.path) -replace '/','\')
     if(!(Test-Path -LiteralPath $check -PathType Leaf) -or
        (Get-FileHash -LiteralPath $check -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){throw 'EDIT_SOURCE_CHANGED'}
    }
   }elseif($job.mode -ne 'READ_ONLY_REVIEW'){throw 'REVIEW_MODE_MISMATCH'}
   $headNow=git -C ([string]$job.repo) rev-parse HEAD
   if($LASTEXITCODE -ne 0 -or $headNow -ne $job.head){throw 'HEAD_CHANGED_REPREPARE'}
   $board='D:\Git PWA\TAKY\TOOLS\TAKY_USAGE_BOARD.py'
   $nowRaw=(& python -X utf8 $board --route-dry-run --task-kind $job.task_kind --task-size $job.task_size --planned-calls ([int]$job.planned_calls) | Out-String)
   if($LASTEXITCODE -ne 0){throw 'USAGE_REFRESH_FAILED'}
   $currentRoute=$nowRaw|ConvertFrom-Json
   if($currentRoute.status -ne 'READY_FOR_SEPARATE_AUTHORIZATION' -or
      $currentRoute.dryRun -ne $true -or $currentRoute.inferenceCalls -ne 0){throw 'USAGE_ROUTE_HOLD'}
   # An AUTO preparation already selected a provider from both usage and
   # signed route health. Do not silently change it to a now-blocked primary.
   $chosen=[string]$job.executor
   if($chosen -notin @('Codex','Claude')){throw 'ROUTE_NOT_RESOLVED'}
   $providerName=if($chosen -eq 'Codex'){'Codex CLI'}else{'Claude Code'}
   $candidate=@($currentRoute.candidates|Where-Object {$_.provider -eq $providerName -and $_.risk -eq 'SAFE'})
   if($candidate.Count -ne 1){throw 'EXECUTOR_QUOTA_UNSAFE_REPREPARE'}
   $routeHealth='D:\Git PWA\TAKY\TOOLS\TAKY_GOVERNED_ROUTE_HEALTH.py'
   $healthRaw=(& python -X utf8 $routeHealth --executor $chosen --repo ([string]$job.repo) | Out-String)
   if($LASTEXITCODE -ne 0){throw 'SIGNED_ROUTE_CHECK_UNAVAILABLE'}
   try{$health=$healthRaw|ConvertFrom-Json}catch{throw 'SIGNED_ROUTE_CHECK_INVALID'}
   if($health.status -ne 'READY_FOR_EXISTING_COST_AND_APPROVAL_GATES'){
     throw ('EXECUTOR_GOVERNANCE_HOLD_REPREPARE: '+[string]$health.reason)
   }
   $result['governed_route_health']=$health
   $result.executor=$chosen
   $result['changed_from_prepared']=$chosen -ne [string]$job.executor
   $result['usage_preflight']=$candidate[0]
   $result['forecast_type']=$currentRoute.forecastType
   $result['task_id']=$job.id
   $result['task_file']=$resolved
   $result['work_id']=Sync-WorkbenchAssignment ([string]$job.id) $resolved $chosen ([string]$job.repo)
   if(!$AuthorizeModelCall){
     $result.status='PREVIEW_ONLY_NOT_EXECUTED'
     $result.output='Fresh quota route verified; no model call; execution requires explicit model authorization'
     break
   }
   if($env:TAKY_USER_EXPLICIT_AUTHORIZATION -ne '1'){throw 'EXPLICIT_AUTHORIZATION_REQUIRED'}
   if($AuthorizeFileApply -and ($job.task_kind -ne 'implementation' -or
      $env:TAKY_ALLOW_SCOPED_FILE_EDIT -ne '1')){throw 'SCOPED_EDIT_AUTHORIZATION_REQUIRED'}
   $execReceipt=Join-Path $history ('TAKY_ROUTED_'+$job.id+'.json')
   # Build and validate bounded correction context before reserving a task receipt.
   # A context lookup failure must not strand an empty in-flight reservation.
   $modelPrompt=[string]$job.task
   if($job.task_kind -eq 'implementation'){
    $paths=@($job.allowed_files|ForEach-Object {[string]$_.path}) -join ', '
    $format='{"task_id":"ID","edits":[{"path":"FILE","replacements":[{"old":"EXACT_SNIPPET","new":"NEW_SNIPPET"}]}]}'
    $modelPrompt="Review code and propose only scoped replacements. Return ONLY a JSON object, no prose or markdown. "+
      "Schema: $format. Replace ID with $($job.id). Paths must be exactly: $paths. "+
      "Old snippets must exist exactly once in provided source. Do not propose edits outside these files. "+
      "TASK: $($job.task) ACCEPTANCE: $($job.acceptance_criteria). SOURCE_FILES: $paths."
    if($modelPrompt.Length -gt 2500){throw 'PROPOSAL_PROMPT_TOO_LARGE'}
   }
   # Existing C2S journal -> bounded task context. Never independent authority.
   $correctionEventIds=@()
   $correctionContextState='NONE'
   $nsMap=@{
     'D:\Git PWA\TAKY'='TAKY_SYSTEMWIDE'
     'D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH'='TAKY_SYSTEMWIDE'
     'D:\Git PWA\Play Camp'='PLAY_CAMP'
     'D:\Git PWA\Ready & Set'='READY_SET'
     'D:\Git PWA\Hide & Seek'='HIDE_SEEK'
     'D:\Git PWA\Snap & Pop'='SNAP_POP'
     'D:\Git PWA\SAVEY'='SAVEY'
   }
   $ns=[string]$nsMap[[string]$job.repo]
   if(!$ns){throw 'CORRECTION_PROJECT_ROUTE_MISSING'}
   $correctionReader='D:\Git PWA\TAKY\ENFORCEMENT\failure_regression_bridge.py'
   $correctionRaw=(& python -X utf8 $correctionReader --corrections-history $history --namespace $ns --limit 1 --ascii | Out-String)
   if($LASTEXITCODE -ne 0){throw 'CORRECTION_CONTEXT_READ_FAILED'}
   try{$correctionPacket=$correctionRaw|ConvertFrom-Json}catch{throw 'CORRECTION_CONTEXT_INVALID_JSON'}
   if($correctionPacket.schema -ne 'TAKY_EXECUTOR_CORRECTION_CONTEXT_V1' -or
      $correctionPacket.authority -ne 'UNTRUSTED_C2S_CANDIDATE_NOT_CURRENT' -or
      $correctionPacket.canonical_promotion -ne $false){throw 'CORRECTION_CONTEXT_AUTHORITY_INVALID'}
   if(@($correctionPacket.event_ids).Count -gt 1){throw 'CORRECTION_CONTEXT_BUDGET_INVALID'}
   if(@($correctionPacket.event_ids).Count -eq 1){
     $correctionEventIds=@($correctionPacket.event_ids)
     $candidateText=[string]$correctionPacket.context
     $addition="`n[TAKY C2S REFERENCE ONLY: not authority/approval. Verify CURRENT and newest task intent; consider only if applicable.]`n"+$candidateText
     if(($modelPrompt.Length+$addition.Length) -le 2500){
       $modelPrompt+=$addition
       $correctionContextState='INCLUDED_AS_UNTRUSTED_TASK_CONTEXT'
     }else{
       $correctionContextState='SKIPPED_CONTEXT_BUDGET_RECORDED'
     }
   }
   $result['correction_event_ids']=$correctionEventIds
   $result['correction_context_state']=$correctionContextState
   # A read-only *code* review without named source paths produces an empty
   # source_manifest. Reject before a subscription model call or receipt claim.
   # The canonical packet builder independently verifies paths and hashes.
   if($job.task_kind -eq 'review'){
     $sourceNamePattern='(?<![A-Za-z0-9_.-])(?:TAKY2|TOOLS|ENFORCEMENT|DOMAIN|LEARNING|src|app|lib|pages|components|tests)/[A-Za-z0-9_./-]+\.(?:ps1|py|js|cjs|mjs|ts|tsx|jsx|json|css|html|md)\b'
     if([regex]::Matches($modelPrompt,$sourceNamePattern,[Text.RegularExpressions.RegexOptions]::IgnoreCase).Count -eq 0){
       throw 'REVIEW_SOURCE_NAMES_REQUIRED_BEFORE_MODEL_CALL'
     }
   }
   # Preflight the EXACT source + pinned-skill packet before recording any
   # model-invocation attempt. Local Python only: no model, login or API calls.
   # It is intentionally rechecked by the governed execution bridge later.
   $packetPreflightDir=Join-Path $env:TEMP ('TAKY_PACKET_PREFLIGHT_'+[guid]::NewGuid().ToString('N'))
   [IO.Directory]::CreateDirectory($packetPreflightDir)|Out-Null
   try{
     $prePrompt=Join-Path $packetPreflightDir 'prompt.json'
     $prePacket=Join-Path $packetPreflightDir 'packet.txt'
     [IO.File]::WriteAllText($prePrompt,(@{prompt=$modelPrompt}|ConvertTo-Json -Depth 3),[Text.UTF8Encoding]::new($false))
     $packetTool='D:\Git PWA\TAKY\TOOLS\TAKY_MODEL_REVIEW_PACKET.py'
     $packetMode=if($job.task_kind -eq 'implementation'){'implementation'}else{'review'}
     # The signed TAKY2 kernel is a sibling repository, not Python's default script path.
     # Scope PYTHONPATH only to this local packet subprocess and restore it afterward.
     $packetRuntimeRoot='D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH'
     if(!(Test-Path -LiteralPath (Join-Path $packetRuntimeRoot 'TAKY2\enforcement.py') -PathType Leaf)){throw 'SIGNED_PACKET_KERNEL_MISSING'}
     $priorPythonPath=[Environment]::GetEnvironmentVariable('PYTHONPATH','Process')
     try {
       $env:PYTHONPATH=$packetRuntimeRoot
       $preResultRaw=(& python -X utf8 $packetTool --repo ([string]$job.repo) --prompt-file $prePrompt --packet-file $prePacket --mode $packetMode | Out-String)
       $packetExit=$LASTEXITCODE
     } finally {
       if($null -eq $priorPythonPath){Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue}
       else {$env:PYTHONPATH=$priorPythonPath}
     }
     if($packetExit -ne 0){throw 'PACKET_PREFLIGHT_FAILED_BEFORE_MODEL_ATTEMPT'}
     try{$packetCheck=$preResultRaw|ConvertFrom-Json}catch{throw 'PACKET_PREFLIGHT_METADATA_INVALID'}
     if($packetCheck.packet_digest -notmatch '^[a-f0-9]{20}$' -or
        @($packetCheck.included_skills).Count -lt 2){throw 'PACKET_PREFLIGHT_BINDING_INVALID'}
     if($job.task_kind -eq 'implementation'){
       $expected=@($job.allowed_files|ForEach-Object {([string]$_.path).Replace('\','/').ToLowerInvariant()})
       $provided=@($packetCheck.included_source_files|ForEach-Object {([string]$_.path).Replace('\','/').ToLowerInvariant()})
       if($expected.Count -ne $provided.Count -or
          @($expected|Where-Object {$provided -cnotcontains $_}).Count -gt 0 -or
          @($packetCheck.included_source_files|Where-Object {$_.complete -ne $true}).Count -gt 0){
         throw 'IMPLEMENTATION_PACKET_SOURCE_SET_OR_COMPLETENESS_MISMATCH'
       }
     }elseif(@($packetCheck.included_source_files).Count -eq 0){
       throw 'REVIEW_PACKET_NO_SOURCE_EVIDENCE'
     }
     $result['packet_preflight']=@{status='LOCAL_COMPLETE_PACKET_READY_NOT_INVOKED'
       packet_digest=[string]$packetCheck.packet_digest
       source_count=@($packetCheck.included_source_files).Count
       packet_chars=[int]$packetCheck.packet_chars}
   }finally{
     Remove-Item -LiteralPath $packetPreflightDir -Recurse -Force -ErrorAction SilentlyContinue
   }
   # Reserve only after the source, skill and complete-packet gates pass.
   try{
     $stream=[IO.File]::Open($execReceipt,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
     $stream.Dispose()
   }catch [IO.IOException]{throw 'TASK_ALREADY_DISPATCHED_OR_RESERVED'}
   $execution=[ordered]@{
     work_id=[string]$result['work_id']
     task_id=$job.id;executor=$chosen;state='STARTED'
     correction_event_ids=$correctionEventIds;correction_context_state=$correctionContextState
     correction_effect_state=$(if($correctionContextState -eq 'INCLUDED_AS_UNTRUSTED_TASK_CONTEXT'){'AWAITING_RESULT_COMPARISON'}else{'NOT_EVALUATED'})
     correction_effect_verified=$false
     started_utc=[DateTime]::UtcNow.ToString('o');result='';exit_code=$null
     quota_before=$candidate[0].beforeUsedPercent
     quota_before_observed_at=$candidate[0].observedAt
     quota_after=$null;quota_after_observed_at=$null
     usage_delta_status='UNMEASURABLE_BEFORE_REFRESH'
   }
   # A reserved, empty file is not a receipt. Record an honest STARTED
   # snapshot before any potentially long/interruptible external call.
   $execution['model_invocation_attempted']=$false
   $execution['model_called']=$null
   [IO.File]::WriteAllText($execReceipt,($execution|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
   $temporary=''
   try{
     $execution['model_invocation_attempted']=$true
     [IO.File]::WriteAllText($execReceipt,($execution|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
     # Bound the *outer* PowerShell wrapper too; TAKY2 already bounds the
     # inner model CLI to 180 seconds. A hung wrapper must not burn CPU forever.
     $runner='D:\Git PWA\TAKY\TOOLS\TAKY_REVIEW_BOUNDED_RUNNER.py'
     $temporary=Join-Path $env:TEMP ('TAKY_BOUNDED_REVIEW_'+$job.id+'.json')
     $payload=@{provider=($(if($chosen -eq 'Codex'){'codex'}else{'claude'}))
                repo=[string]$job.repo;prompt=$modelPrompt;task_id=[string]$job.id
                outputMode=$(if($job.task_kind -eq 'implementation'){'Raw'}else{'Envelope'})
                timeoutSeconds=$(if($job.task_kind -eq 'review') {90} else {180})}
     if($job.task_kind -eq 'implementation'){
       $payload['scopedEditTaskSha256']=(Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant()
     }
     [IO.File]::WriteAllText($temporary,($payload|ConvertTo-Json -Depth 4),
       [Text.UTF8Encoding]::new($false))
     $runRaw=(& python -X utf8 $runner --request $temporary | Out-String)
     if($LASTEXITCODE -ne 0){throw 'BOUNDED_REVIEW_RUNNER_FAILED_UNKNOWN_OUTCOME'}
     $run=$runRaw|ConvertFrom-Json
     if([string]$run.task_id -cne [string]$job.id){throw 'BOUNDED_RUN_TASK_ID_MISMATCH'}
     if($run.governedReceipt){
       if([string]$run.governedReceipt.task_id -cne [string]$job.id){throw 'GOVERNED_RECEIPT_TASK_ID_MISMATCH'}
       if([string]$run.governedReceipt.packet_digest -cne [string]$packetCheck.packet_digest){
         throw 'PREFLIGHT_TO_EXECUTION_PACKET_DIGEST_DRIFT_OUTCOME_UNKNOWN'
       }
       $execution['taky2_receipt_id']=[string]$run.governedReceipt.receipt_id
       $execution['taky2_receipt_state']=[string]$run.governedReceipt.executor_state
       if($run.governedReceipt.call_manifest){
         $execution['governed_call_manifest']=$run.governedReceipt.call_manifest
       }
       if($run.governedReceipt.packet_digest -and $null -ne $run.governedReceipt.source_manifest){
         $execution['review_source_binding']=@{packet_digest=[string]$run.governedReceipt.packet_digest;
           source_manifest=@($run.governedReceipt.source_manifest)}
         if($run.governedReceipt.skill_manifest){
           $execution['review_source_binding']['skill_manifest']=@($run.governedReceipt.skill_manifest)
         }
       }
     }else{$execution['taky2_receipt_state']='NOT_OBSERVED'}
     $execution['signed_readback_state']=[string]$run.signedReadback.state
     if($run.signedReadback.receiptId){
       if($run.governedReceipt -and [string]$run.governedReceipt.receipt_id -cne [string]$run.signedReadback.receiptId){throw 'GOVERNED_SIGNED_RECEIPT_CONFLICT'}
       $execution['taky2_signed_receipt_id']=[string]$run.signedReadback.receiptId
     }
     $expectedModel=if($chosen -eq 'Codex'){'codex'}else{'sonnet'}
     # Signed CLI return is not sufficient if the very packet/call manifest
     # handed to the provider has not been correlated with the sealed ledger.
     $signedCliReturned=($run.signedReadback.state -eq 'CLI_RETURNED_UNVERIFIED' -and
       $run.signedReadback.preflightAllowed -eq $true -and $run.signedReadback.callAllowed -eq $true -and
       $run.signedReadback.signedCallManifestBound -eq $true -and
       [string]$run.signedReadback.model -eq $expectedModel -and $run.signedReadback.cliExitCode -eq 0)
     $execution['transport_status']=[string]$run.status
     $execution['elapsed_seconds']=$run.elapsedSeconds
     $execution['resource_limit_breach']=[string]$run.resourceLimitBreach
     $execution['peak_child_memory_mb']=$run.peakChildMemoryMb
     $execution.exit_code=$run.returncode
     $summary=[string]$run.stdout
     if($run.stderr){$summary+='; STDERR: '+[string]$run.stderr}
     $execution.result=$summary.Substring(0,[Math]::Min($summary.Length,3000))
     $execution.state=if($run.timeout -eq $true -or $run.resourceLimitBreach){'OUTCOME_UNKNOWN'
          }elseif($run.status -eq 'RETURNED_UNVERIFIED' -and -not $signedCliReturned){'OUTCOME_UNKNOWN'
          }elseif($run.status -eq 'RETURNED_UNVERIFIED' -and $run.returncode -eq 0 -and $signedCliReturned){
          'COMPLETE_UNVERIFIED'}else{'FAILED'}
     if($execution.state -eq 'COMPLETE_UNVERIFIED' -and $job.task_kind -eq 'review'){
       # A returned CLI is transport success, not accepted content. Inspect
       # explicitly cited, supplied source files without another model call.
       $execution['content_qa_state']='NO_NAMED_SOURCE_HOLD'
       try{
         $sourcePattern='(?i)(?<![A-Za-z0-9_.-])((?:TAKY2|TOOLS|ENFORCEMENT|DOMAIN|LEARNING|src|app|lib|pages|components|tests)/[A-Za-z0-9_./-]+\.(?:py|ps1|js|ts|tsx|jsx|json|css|html|md))\b'
         $sourceNames=@([regex]::Matches($modelPrompt,$sourcePattern) |
              ForEach-Object {$_.Groups[1].Value} | Select-Object -Unique)
         if($sourceNames.Count -ge 1 -and $sourceNames.Count -le 2){
           $qaTool='D:\Git PWA\TAKY\TOOLS\TAKY_REVIEW_EVIDENCE_QA.py'
           $qaArgs=@($qaTool,'--task-id',[string]$job.id,'--repo',[string]$job.repo)
           foreach($sourceName in $sourceNames){$qaArgs+=@('--source',[string]$sourceName)}
           $bindingPath=''
           try{
             if($execution.Contains('review_source_binding')){
               $bindingPath=Join-Path $env:TEMP ('TAKY_QA_BIND_'+$job.id+'.json')
               [IO.File]::WriteAllText($bindingPath,($execution['review_source_binding']|ConvertTo-Json -Depth 6),
                 [Text.UTF8Encoding]::new($false))
               $qaArgs+=@('--binding-file',$bindingPath)
             }
             $qaRaw=(& python -X utf8 @qaArgs | Out-String)
           }finally{
             if($bindingPath){Remove-Item -LiteralPath $bindingPath -Force -ErrorAction SilentlyContinue}
           }
           if($LASTEXITCODE -ne 0){throw 'CONTENT_QA_PROCESS_FAILED'}
           $qa=$qaRaw|ConvertFrom-Json
           if($qa.signedRuntimeIntegrity -ne 'PASS' -or [string]$qa.taskId -cne [string]$job.id -or
             [string]$qa.receiptId -cne [string]$execution['taky2_signed_receipt_id']){
             throw 'CONTENT_QA_SIGNED_RECEIPT_UNVERIFIED'
           }
           $execution['content_qa_state']=[string]$qa.state
           $execution['content_qa_invalid_citations']=@($qa.invalidCitations)
           $execution['content_qa_response_sha256']=[string]$qa.responseSha256
           $execution['content_quality_verified']=$false
         }elseif($sourceNames.Count -gt 2){
           $execution['content_qa_state']='MULTIPLE_UNBOUNDED_SOURCES_HOLD'
         }
       }catch{
         $execution['content_qa_state']='CONTENT_QA_UNAVAILABLE_HOLD'
         $execution['content_quality_verified']=$false
       }
     }
     if($execution.state -eq 'COMPLETE_UNVERIFIED' -and $job.task_kind -eq 'implementation'){
      if($run.outputTruncated){throw 'MODEL_PROPOSAL_TRUNCATED'}
      $proposalPath=Join-Path $inbox ($job.id+'.edit.json')
      $rawFile=Join-Path $env:TEMP ('TAKY_EDIT_MODEL_'+$job.id+'.txt')
      try{
       [IO.File]::WriteAllText($rawFile,([string]$run.stdout),[Text.UTF8Encoding]::new($false))
       $proposalRaw=(& python -X utf8 'D:\Git PWA\TAKY\TOOLS\TAKY_SCOPED_EDIT_APPLY.py' --task-file $resolved --extract-output-file $rawFile --candidate-file $proposalPath | Out-String)
       $proposalResult=$proposalRaw|ConvertFrom-Json
       if($proposalResult.status -ne 'PROPOSAL_VALIDATED_NOT_APPLIED'){throw ('MODEL_PROPOSAL_REJECTED: '+[string]$proposalResult.reason)}
       $execution.state='PROPOSAL_VALIDATED_NOT_APPLIED'
       $execution['proposal_file']=$proposalPath
       if($AuthorizeFileApply){
        if(-not $execution['taky2_signed_receipt_id']){throw 'SCOPED_EDIT_SIGNED_RECEIPT_MISSING'}
        # The verifier binds the exact model output, source snapshot and task
        # against TAKY2's sealed preflight before any file is replaced.
        [IO.File]::WriteAllText($execReceipt,($execution|ConvertTo-Json -Depth 9),
          [Text.UTF8Encoding]::new($false))
        $applyRaw=(& python -X utf8 'D:\Git PWA\TAKY\TOOLS\TAKY_SCOPED_EDIT_APPLY.py' --task-file $resolved --proposal-file $proposalPath --apply --signed-receipt ([string]$execution['taky2_signed_receipt_id']) --execution-record $execReceipt | Out-String)
        $applyResult=$applyRaw|ConvertFrom-Json
        if($applyResult.status -ne 'APPLIED_UNVERIFIED'){throw ('LOCAL_SCOPED_EDIT_HOLD: '+[string]$applyResult.reason)}
        $execution.state='APPLIED_UNVERIFIED'
        $execution['changed_files']=$applyResult.files
       }
      }catch{
       $execution.state='PROPOSAL_REJECTED'
       $execution['proposal_error']=$_.Exception.Message
      }finally{Remove-Item -LiteralPath $rawFile -Force -ErrorAction SilentlyContinue}
     }
   }catch{
     # After intent-to-invoke was persisted, a wrapper exception does not
     # prove that the external model was never reached. Fail closed.
     $execution.state='OUTCOME_UNKNOWN'
     $execution.result='WRAPPER_ERROR_UNCERTAIN_EXECUTION: '+$_.Exception.Message
   }finally{
     if($temporary){Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue}
     # The monitor refresh interval may exceed the task runtime. Never treat a
     # quota snapshot delta as exclusively attributable to this task.
     try{
       $nextRaw=(& python -X utf8 $board --route-dry-run --task-kind $job.task_kind --task-size $job.task_size --planned-calls ([int]$job.planned_calls)|Out-String)
       if($LASTEXITCODE -eq 0){
         $nextRoute=$nextRaw|ConvertFrom-Json
         $nextCandidate=@($nextRoute.candidates|Where-Object {$_.provider -eq $providerName})
         if($nextCandidate.Count -eq 1){
           $execution.quota_after=$nextCandidate[0].beforeUsedPercent
           $execution.quota_after_observed_at=$nextCandidate[0].observedAt
           $execution.usage_delta_status=if($execution.quota_before_observed_at -eq $execution.quota_after_observed_at){'SAME_CACHED_SNAPSHOT_NO_ESTIMATE'}else{'CHANGED_SNAPSHOT_NOT_TASK_ATTRIBUTED'}
         }
       }
     }catch{$execution.usage_delta_status='AFTER_OBSERVATION_UNAVAILABLE'}
     $execution['finished_utc']=[DateTime]::UtcNow.ToString('o')
     [IO.File]::WriteAllText($execReceipt,($execution|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
   }
   $result.status=$execution.state
   $result.model_called=$null
   $result['model_invocation_attempted']=$true
   $result.output='Executor wrapper returned; actual inference and task success require receipt verification'
   $result['execution_receipt']=$execReceipt
   if($execution.Contains('proposal_file')){$result['proposal_file']=$execution.proposal_file}
   if($execution.Contains('changed_files')){$result['changed_files']=$execution.changed_files}
  }
  'Dispatch' {
   if([string]::IsNullOrWhiteSpace($Task)){throw 'Task required'}
   # A model call remains behind the existing explicit approval and receipt bridge.
   # Preparing a request is safe and does not launch an inference process.
   if($AuthorizeModelCall -and $env:TAKY_USER_EXPLICIT_AUTHORIZATION -ne '1'){throw 'EXPLICIT_AUTHORIZATION_REQUIRED'}
   $prepare='D:\Git PWA\TAKY\TOOLS\taky_chat_task_prepare.ps1'
   if($TaskKind -eq 'validation'){
    $raw=(& $prepare -Task $Task -TaskKind validation -Repo $Repo -DryRun | Out-String)
    $local=$raw|ConvertFrom-Json
    if($local.status -ne 'LOCAL_ONLY_NO_MODEL_TASK'){throw 'LOCAL_ROUTE_UNAVAILABLE'}
    $result.executor='LOCAL_DETERMINISTIC'
    # A local route alone is NOT completed work. Execute one explicitly bounded
    # syntax/data validation without an AI call when the user named the files.
    if($AllowedFiles.Count -eq 0){
      $result.status='LOCAL_ONLY_NO_MODEL_TASK'
      $result.output='No source files named. No validation executed; specify files and SYNTAX_ONLY.'
      break
    }
    if($AcceptanceCriteria -ceq 'TABLET_SMOKE'){
      # Existing, fixed Play Camp browser journey only: no arbitrary commands,
      # no model, no deploy. Browser viewport is not a physical tablet.
      if($Repo -cne 'D:\Git PWA\Play Camp' -or $AllowedFiles.Count -ne 1 -or
         [string]$AllowedFiles[0] -cne 'scripts/smoke-tablet.mjs'){
        throw 'LOCAL_TABLET_SMOKE_SCOPE_INVALID'
      }
      $nodeExe='C:\Program Files\nodejs\node.exe'
      $scriptFile=Join-Path $Repo 'scripts\smoke-tablet.mjs'
      $buildFile=Join-Path $Repo 'dist\index.html'
      if(!(Test-Path -LiteralPath $nodeExe -PathType Leaf) -or
         !(Test-Path -LiteralPath $scriptFile -PathType Leaf) -or
         !(Test-Path -LiteralPath $buildFile -PathType Leaf)){
        throw 'LOCAL_TABLET_SMOKE_BUILD_OR_BINARY_MISSING'
      }
      $before=@{}
      foreach($rel in @('scripts/smoke-tablet.mjs','dist/index.html')){
        $path=Join-Path $Repo ($rel -replace '/','\')
        if(((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
          throw 'LOCAL_TABLET_SMOKE_UNTRUSTED_SOURCE'
        }
        $before[$rel]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
      }
      $stdout=Join-Path $env:TEMP ('TAKY_TABLET_SMOKE_'+$id+'.log')
      $stderr=Join-Path $env:TEMP ('TAKY_TABLET_SMOKE_'+$id+'.err')
      $oldViewport=$env:PLAY_CAMP_SMOKE_VIEWPORT
      $oldOptions=$env:NODE_OPTIONS
      $watch=[Diagnostics.Stopwatch]::StartNew()
      $runStart=[DateTime]::UtcNow
      $proc=$null
      try{
        $env:PLAY_CAMP_SMOKE_VIEWPORT='1180x820'
        $env:NODE_OPTIONS=$null
        $proc=Start-Process -FilePath $nodeExe -ArgumentList @('scripts/smoke-tablet.mjs') `
          -WorkingDirectory $Repo -RedirectStandardOutput $stdout -RedirectStandardError $stderr `
          -WindowStyle Hidden -PassThru
        if(!$proc.WaitForExit(150000)){
          & taskkill.exe /PID $proc.Id /T /F >$null 2>$null
          throw 'LOCAL_TABLET_SMOKE_TIMEOUT_150S_HOLD'
        }
        $proc.Refresh()
        $exitCode=[int]$proc.ExitCode
        if((Get-Item -LiteralPath $stdout).Length -gt 120000){throw 'LOCAL_TABLET_SMOKE_LOG_OVERSIZE'}
        $browserLog=Get-Content -LiteralPath $stdout -Raw -Encoding UTF8
        $sourceUnchanged=$true
        foreach($rel in @($before.Keys)){
          $path=Join-Path $Repo ($rel -replace '/','\')
          if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $before[$rel]){
            $sourceUnchanged=$false
          }
        }
        $captures=@()
        foreach($rel in @('artifacts/trail-mirror-ink-1180x820.png',
                          'artifacts/trail-dot-copy-1180x820.png',
                          'artifacts/trail-shared-island-cold-1180x820.png')){
          $path=Join-Path $Repo ($rel -replace '/','\')
          if(Test-Path -LiteralPath $path -PathType Leaf){
            $item=Get-Item -LiteralPath $path
            if($item.LastWriteTimeUtc -ge $runStart -and $item.Length -gt 5000){
              $captures+=@{path=$rel;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
            }
          }
        }
        $passed=($exitCode -eq 0 -and $sourceUnchanged -and $captures.Count -eq 3 -and
          $browserLog -match '(?m)^1180x820 PASS\s*$')
        $result['model_calls']=0
        $result['local_validation_scope']='PLAY_CAMP_CHROMIUM_BROWSER_1180x820_NOT_PHYSICAL_TABLET'
        $result['source_hashes']=$before
        $result['browser_captures']=$captures
        $result['tests_executed']=1
        $result['tests_passed']=if($passed){1}else{0}
        $result['elapsed_seconds']=[Math]::Round($watch.Elapsed.TotalSeconds,3)
        $result['test_exit_code']=$exitCode
        $result.status=if($passed){'LOCAL_VALIDATION_PASS'}else{'LOCAL_VALIDATION_HOLD'}
        $result.output=if($passed){'Play Camp actual Chromium end-to-end journey passed and screenshots hash-bound; physical device and design approval open'}else{'Play Camp browser journey failed, evidence missing, or source changed'}
      }finally{
        $watch.Stop()
        $env:PLAY_CAMP_SMOKE_VIEWPORT=$oldViewport
        $env:NODE_OPTIONS=$oldOptions
        if($proc){$proc.Dispose()}
        Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
      }
      break
    }
    if($AcceptanceCriteria -ceq 'FLIPBOOK_SMOKE'){
      # Existing Play Camp browser journey, not a new harness. No model call.
      if($Repo -cne 'D:\Git PWA\Play Camp' -or @($AllowedFiles).Count -ne 1 -or
         [string]$AllowedFiles[0] -cne 'scripts/smoke-hangul-flipbook.mjs'){
        throw 'FLIPBOOK_SMOKE_SCOPE_NOT_ALLOWLISTED'
      }
      $nodeExe='C:\Program Files\nodejs\node.exe'
      $script=Join-Path $Repo 'scripts\smoke-hangul-flipbook.mjs'
      $index=Join-Path $Repo 'dist\index.html'
      foreach($p in @($nodeExe,$script,$index)){
        if(!(Test-Path -LiteralPath $p -PathType Leaf) -or
           ((Get-Item -LiteralPath $p).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
          throw 'FLIPBOOK_SMOKE_BINARY_OR_BUILD_MISSING'
        }
      }
      $scriptSha=(Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash.ToLowerInvariant()
      $buildSha=(Get-FileHash -LiteralPath $index -Algorithm SHA256).Hash.ToLowerInvariant()
      $stdout=Join-Path $env:TEMP ('TAKY_FLIPBOOK_'+$id+'.out')
      $stderr=Join-Path $env:TEMP ('TAKY_FLIPBOOK_'+$id+'.err')
      $runStarted=[DateTime]::UtcNow
      $watch=[Diagnostics.Stopwatch]::StartNew()
      $proc=$null
      try{
        $proc=Start-Process -FilePath $nodeExe -ArgumentList @('scripts/smoke-hangul-flipbook.mjs') `
          -WorkingDirectory $Repo -RedirectStandardOutput $stdout -RedirectStandardError $stderr `
          -WindowStyle Hidden -PassThru
        if(!$proc.WaitForExit(90000)){
          & taskkill.exe /PID $proc.Id /T /F >$null 2>$null
          throw 'FLIPBOOK_SMOKE_TIMEOUT_90S_HOLD'
        }
        $proc.Refresh()
        $exit=[int]$proc.ExitCode
        if((Get-Item -LiteralPath $stdout).Length -gt 30000){throw 'FLIPBOOK_SMOKE_LOG_TOO_LARGE'}
        $log=Get-Content -LiteralPath $stdout -Raw -Encoding UTF8
        $artifacts=@()
        $widths=@(1280,1024,390)
        $fresh=$true
        foreach($width in $widths){
          foreach($kind in @('hangul-flipbook','hangul-flipbook-midturn','hangul-compound')){
            $rel=('artifacts/'+$kind+'-'+$width+'.png')
            $shot=Join-Path $Repo ($rel -replace '/','\')
            if(!(Test-Path -LiteralPath $shot -PathType Leaf)){ $fresh=$false;continue }
            $item=Get-Item -LiteralPath $shot
            if($item.LastWriteTimeUtc -lt $runStarted -or $item.Length -lt 5000 -or
               (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)){
              $fresh=$false;continue
            }
            $artifacts+=@{path=$rel;sha256=(Get-FileHash -LiteralPath $shot -Algorithm SHA256).Hash.ToLowerInvariant()}
          }
        }
        $sourceStable=(
           (Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $scriptSha -and
           (Get-FileHash -LiteralPath $index -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $buildSha
        )
        $allPass=($exit -eq 0 -and $fresh -and $sourceStable -and $artifacts.Count -eq 9)
        foreach($width in $widths){
          if($log -notmatch ('(?m)^PASS '+$width+' basic \+ independent compound-paper assembly result ')){
            $allPass=$false
          }
        }
        $result['model_calls']=0
        $result['tests_executed']=3
        $result['tests_passed']=if($allPass){3}else{0}
        $result['test_exit_code']=$exit
        $result['verified_files']=@(@{path='scripts/smoke-hangul-flipbook.mjs';sha256=$scriptSha})
        $result['browser_captures']=$artifacts
        $result['elapsed_seconds']=[Math]::Round($watch.Elapsed.TotalSeconds,2)
        $result['baseline_state']='NOT_CAPTURED'
        $result['design_parity_state']='UNVERIFIED'
        $result['correction_effect_verified']=$false
        $result['test_source_unchanged']=$sourceStable
        $result.status=if($allPass){'LOCAL_VALIDATION_PASS'}else{'LOCAL_VALIDATION_HOLD'}
        $result.output=if($allPass){'Play Camp flipbook behavior passed in real Chromium at 1280, 1024, 390; baseline/design parity remain unverified'}else{'Flipbook browser behavior, source binding, or screenshot evidence failed'}
      }finally{
        $watch.Stop()
        if($proc){$proc.Dispose()}
        Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
      }
      break
    }
    if($AcceptanceCriteria -ceq 'UNIT_TESTS'){
      # Specific Play Camp learning-domain tests; do not execute arbitrary files,
      # scripts, package scripts or user-supplied shell commands.
      if($Repo -cne 'D:\Git PWA\Play Camp' -or $AllowedFiles.Count -gt 2){
        throw 'LOCAL_FUNCTION_TEST_APPROVED_REPO_AND_TWO_FILES_REQUIRED'
      }
      $approvedCases=@{
        'tests/hangul.test.ts'=@('src/lib/hangul.ts')
        'tests/paperFoldGeometry.test.ts'=@('src/activities/paperFoldGeometry.ts','src/data/activityRegistry.ts','src/domain/activity.ts')
        'tests/matchstick.test.ts'=@('src/activities/matchstick.ts')
        'tests/matchstickSolver.test.ts'=@('src/activities/matchstick.ts','src/activities/matchstickSolver.ts')
        'tests/cubeNetGeometry.test.ts'=@('src/activities/cubeNetGeometry.ts','src/activities/cubeHingeMoves.ts')
      }
      $nodeExe='C:\Program Files\nodejs\node.exe'
      if(!(Test-Path -LiteralPath $nodeExe -PathType Leaf)){throw 'LOCAL_NODE_PINNED_BINARY_MISSING'}
      $testFiles=@()
      $hashes=@()
      $domainDeps=@($AllowedFiles|ForEach-Object{$approvedCases[[string]$_]}|Select-Object -Unique)
      $dependencyHashes=@()
      foreach($relSource in $domainDeps){
        $sourcePath=Join-Path $Repo ($relSource -replace '/','\')
        $sourceItem=Get-Item -LiteralPath $sourcePath -ErrorAction Stop
        if($sourceItem.Length -gt 100000 -or
           (($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)){
          throw 'LOCAL_DOMAIN_DEPENDENCY_NOT_TRUSTED'
        }
        $dependencyHashes+=@{path=$relSource;sha256=(Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()}
      }
      $seen=[System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
      foreach($name in $AllowedFiles){
        if($name -cnotin @($approvedCases.Keys) -or !$seen.Add($name)){
          throw 'LOCAL_FUNCTION_TEST_NOT_IN_APPROVED_SET'
        }
        $p=Join-Path $Repo ($name -replace '/','\')
        $item=Get-Item -LiteralPath $p -ErrorAction Stop
        if(!$item -or !$item.Exists -or $item.Length -gt 20000 -or
          (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)){
          throw 'LOCAL_FUNCTION_TEST_FILE_NOT_TRUSTED'
        }
        $hashes+=@{path=$name;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
        $testFiles+=('"'+$p+'"')
      }
      $stdout=Join-Path $env:TEMP ('TAKY_LOCAL_TEST_'+$id+'.tap')
      $stderr=Join-Path $env:TEMP ('TAKY_LOCAL_TEST_'+$id+'.err')
      $watch=[Diagnostics.Stopwatch]::StartNew()
      $originalNodeOptions=$env:NODE_OPTIONS
      try{
        $env:NODE_OPTIONS=$null
        $argList=@('--test','--test-reporter=tap')+$testFiles
        $proc=Start-Process -FilePath $nodeExe -ArgumentList $argList -WorkingDirectory $Repo -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
        if(!$proc.WaitForExit(15000)){
          & taskkill.exe /PID $proc.Id /T /F >$null 2>$null
          throw 'LOCAL_TEST_TIMEOUT_15S_HOLD'
        }
        $watch.Stop()
        $proc.Refresh()
        $nodeExit=[int]$proc.ExitCode
        if((Get-Item -LiteralPath $stdout).Length -gt 60000){throw 'LOCAL_TEST_OUTPUT_OVERSIZE'}
        $tap=Get-Content -LiteralPath $stdout -Raw -Encoding UTF8
        $nTests=[regex]::Match($tap,'(?m)^# tests (\d+)\s*$')
        $nPass=[regex]::Match($tap,'(?m)^# pass (\d+)\s*$')
        $nFail=[regex]::Match($tap,'(?m)^# fail (\d+)\s*$')
        foreach($h in @($hashes)+@($dependencyHashes)){
          $q=Join-Path $Repo ($h.path -replace '/','\')
          if((Get-FileHash -LiteralPath $q -Algorithm SHA256).Hash.ToLowerInvariant() -cne $h.sha256){
            throw 'LOCAL_FUNCTION_TEST_SOURCE_CHANGED_HOLD'
          }
        }
        $passed=($nodeExit -eq 0 -and $nTests.Success -and $nPass.Success -and
          $nFail.Success -and [int]$nTests.Groups[1].Value -gt 0 -and
          [int]$nTests.Groups[1].Value -eq [int]$nPass.Groups[1].Value -and
          [int]$nFail.Groups[1].Value -eq 0)
        $result['model_calls']=0
        $result['local_validation_scope']='PLAY_CAMP_SELECTED_DOMAIN_UNIT_TESTS_NOT_BROWSER_E2E'
        $result['verified_files']=$hashes
        $result['source_dependency_hashes']=$dependencyHashes
        $result['files_checked']=$hashes.Count
        $result['tests_executed']=if($nTests.Success){[int]$nTests.Groups[1].Value}else{0}
        $result['tests_passed']=if($nPass.Success){[int]$nPass.Groups[1].Value}else{0}
        $result['tests_failed']=if($nFail.Success){[int]$nFail.Groups[1].Value}else{$null}
        $result['elapsed_seconds']=[Math]::Round($watch.Elapsed.TotalSeconds,3)
        $result['test_exit_code']=$nodeExit
        $result.status=if($passed){'LOCAL_VALIDATION_PASS'}else{'LOCAL_VALIDATION_HOLD'}
        $result.output=if($passed){'Play Camp selected learning logic tests passed; not UI or device acceptance'}else{'Play Camp unit tests failed or produced incomplete TAP result'}
      }finally{
        $env:NODE_OPTIONS=$originalNodeOptions
        if($proc){$proc.Dispose()}
        Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
      }
      break
    }
    if($AllowedFiles.Count -gt 2 -or $AcceptanceCriteria -cne 'SYNTAX_ONLY'){
      throw 'LOCAL_VALIDATION_SCOPE_REQUIRES_ONE_OR_TWO_FILES_AND_SYNTAX_ONLY'
    }
    $repoRoot=[IO.Path]::GetFullPath($Repo).TrimEnd('\')+'\'
    $pythonExe='C:\Python314\python.exe'
    if(!(Test-Path -LiteralPath $pythonExe -PathType Leaf)){throw 'LOCAL_PYTHON_PINNED_BINARY_MISSING'}
    $seen=[System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $findings=@()
    foreach($rel in $AllowedFiles){
      if($rel -cnotmatch '^[A-Za-z0-9_./-]+$' -or $rel -match '(^|/)\.\.(/|$)' -or
         $rel.StartsWith('/') -or !$seen.Add($rel)){throw 'LOCAL_VALIDATION_UNSAFE_RELATIVE_FILE'}
      $resolvedFile=[IO.Path]::GetFullPath((Join-Path $Repo ($rel -replace '/','\')))
      if(!$resolvedFile.StartsWith($repoRoot,[StringComparison]::OrdinalIgnoreCase) -or
         !(Test-Path -LiteralPath $resolvedFile -PathType Leaf)){throw 'LOCAL_VALIDATION_FILE_UNAVAILABLE'}
      if((Get-Item -LiteralPath $resolvedFile).Length -gt 100000){throw 'LOCAL_VALIDATION_FILE_OVERSIZE'}
      $walk=$resolvedFile
      while($walk.StartsWith($repoRoot,[StringComparison]::OrdinalIgnoreCase)){
        if(((Get-Item -LiteralPath $walk).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
          throw 'LOCAL_VALIDATION_REPARSE_POINT_HOLD'
        }
        $walk=[IO.Path]::GetDirectoryName($walk)
        if(!$walk){break}
      }
      $sourceBefore=(Get-FileHash -LiteralPath $resolvedFile -Algorithm SHA256).Hash.ToLowerInvariant()
      $ext=[IO.Path]::GetExtension($resolvedFile).ToLowerInvariant()
      $syntax='UNSUPPORTED'
      if($ext -eq '.py'){
        & $pythonExe -I -X utf8 -m ast $resolvedFile >$null 2>$null
        $valid=($LASTEXITCODE -eq 0)
        $syntax='PYTHON_AST'
      }elseif($ext -eq '.ps1'){
        $tok=$null;$errs=$null
        [void][System.Management.Automation.Language.Parser]::ParseFile($resolvedFile,[ref]$tok,[ref]$errs)
        $valid=(@($errs).Count -eq 0)
        $syntax='POWERSHELL_AST'
      }elseif($ext -in @('.js','.mjs','.cjs')){
        $nodeExe='C:\Program Files\nodejs\node.exe'
        if(!(Test-Path -LiteralPath $nodeExe -PathType Leaf)){throw 'LOCAL_NODE_PINNED_BINARY_MISSING'}
        $nodeOptionsBefore=$env:NODE_OPTIONS
        try {
          $env:NODE_OPTIONS=$null
          & $nodeExe --check $resolvedFile 2>$null
          $valid=($LASTEXITCODE -eq 0)
        } finally {$env:NODE_OPTIONS=$nodeOptionsBefore}
        $syntax='NODE_CHECK'
      }elseif($ext -eq '.json'){
        & $pythonExe -I -X utf8 -m json.tool $resolvedFile >$null 2>$null
        $valid=($LASTEXITCODE -eq 0)
        $syntax='JSON_PARSE'
      }else{throw 'LOCAL_VALIDATION_EXTENSION_UNSUPPORTED'}
      $sourceAfter=(Get-FileHash -LiteralPath $resolvedFile -Algorithm SHA256).Hash.ToLowerInvariant()
      if($sourceAfter -cne $sourceBefore){throw 'LOCAL_SOURCE_CHANGED_DURING_VALIDATION'}
      $findings+=@{path=$rel;sha256=$sourceAfter
                   check=$syntax;passed=[bool]$valid}
    }
    $result['local_validation_scope']='SYNTAX_ONLY_NOT_FUNCTIONAL_QA'
    $result['verified_files']=$findings
    $result['files_checked']=$findings.Count
    $result['model_calls']=0
    $result.status=if(@($findings|Where-Object {!$_.passed}).Count -eq 0){'LOCAL_VALIDATION_PASS'}else{'LOCAL_VALIDATION_HOLD'}
    $result.output=if($result.status -eq 'LOCAL_VALIDATION_PASS'){'Syntax verified locally; app behavior not tested'}else{'Local syntax errors found; app behavior not tested'}
    break
   }
   if($TaskKind -eq 'review'){
     if($AllowedFiles.Count -ne 0){throw 'REVIEW_CANNOT_EDIT'}
     $raw=(& $prepare -Task $Task -Executor $Executor -TaskKind $TaskKind -TaskSize $TaskSize -PlannedCalls $PlannedCalls -Repo $Repo -PortfolioTaskId $PortfolioTaskId | Out-String)
   }else{
     $raw=(& $prepare -Task $Task -Executor $Executor -TaskKind $TaskKind -TaskSize $TaskSize -PlannedCalls $PlannedCalls -Repo $Repo -AllowedFiles $AllowedFiles -AcceptanceCriteria $AcceptanceCriteria -PortfolioTaskId $PortfolioTaskId | Out-String)
   }
   if($LASTEXITCODE -ne 0){throw 'TASK_PREP_FAILED'}
   $prepared=$raw|ConvertFrom-Json
   if($prepared.status -eq 'REUSED_PREPARED_NOT_EXECUTED'){
     # Reusing a prepared request must not be mistaken for an execution.
     $saved=Get-Content -LiteralPath ([string]$prepared.task_file) -Raw -Encoding UTF8 | ConvertFrom-Json
     if($saved.state -ne 'PREPARED_NOT_EXECUTED' -or $saved.id -ne $prepared.id -or
        $saved.task -cne $Task -or $saved.repo -ne $Repo -or
        $saved.executor -notin @('Claude','Codex')){throw 'REUSED_PREPARED_TASK_MISMATCH'}
     $result['preparation_reused']=$true
     $result.executor=$saved.executor
   }elseif($prepared.state -eq 'PREPARED_NOT_EXECUTED'){
     $result['preparation_reused']=$false
     $result.executor=$prepared.executor
   }else{throw 'TASK_NOT_READY'}
   $result.status='PREPARED_NOT_EXECUTED'
   $result['task_id']=$prepared.id
   $result['portfolio_task_id']=$PortfolioTaskId
   $result['task_file']=$prepared.task_file
   $result['work_id']=Sync-WorkbenchAssignment ([string]$prepared.id) ([string]$prepared.task_file) ([string]$result.executor) $Repo
   $result.output='Task prepared and registered to WORKBENCH; no model called; separate authorization required'
   if($AuthorizeModelCall){
    $runRaw=(& $PSCommandPath -Action RunPrepared -TaskFile ([string]$prepared.task_file) -Repo $Repo -AuthorizeModelCall -AuthorizeFileApply:$AuthorizeFileApply | Out-String)
    $runResult=$runRaw|ConvertFrom-Json
    $result.status=[string]$runResult.status
    $result.executor=$runResult.executor
    $result.model_called=$runResult.model_called
    $result['run_receipt']=$runResult.execution_receipt
    $result.output=[string]$runResult.output
    if($runResult.status -eq 'HOLD'){throw ('RUN_PREPARED_HOLD: '+[string]$runResult.output)}
   }
  }
 }
 if($result.status -eq 'STARTED'){$result.status='PASS'}
} catch {
 $result.status='HOLD'
 $result.output=$_.Exception.Message
}
$result.finished_utc=[DateTime]::UtcNow.ToString('o')
if($Action -notin @('Intake','RouteDryRun','Status','AdvanceLocal','ContinueLocal')){
 $path=Join-Path $history "TAKY_CHAT_ORCH_$id.json"
 [System.IO.File]::WriteAllText($path,($result|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
 if($result.Contains('work_id') -and $result.Contains('task_file')){
  try{
   $linked=Sync-WorkbenchAssignment ([string]$result.task_id) ([string]$result.task_file) ([string]$result.executor) $Repo $path
   if($linked -cne [string]$result['work_id']){throw 'WORK_ID_READBACK_MISMATCH'}
  }catch{
   $result.status='HOLD'
   $result.output='WORK_EVIDENCE_LINK_FAILED: '+$_.Exception.Message
   [System.IO.File]::WriteAllText($path,($result|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
  }
 }
}
$result | ConvertTo-Json -Depth 12
