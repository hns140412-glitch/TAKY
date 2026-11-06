param(
 [Parameter(Mandatory=$true)][string]$Task,
 [ValidateSet('Auto','Claude','Codex')][string]$Executor='Auto',
 [ValidateSet('code','implementation','review','validation')][string]$TaskKind='code',
 [ValidateSet('small','medium','large')][string]$TaskSize='medium',
 [ValidateRange(1,4)][int]$PlannedCalls=1,
 [string]$Repo='D:\Git PWA\TAKY',
 [string[]]$AllowedFiles=@(),
 [string]$AcceptanceCriteria='',
 [string]$PortfolioTaskId='',
 [string]$QueueRoot='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\01_INBOX\AI_TASKS',
 [switch]$DryRun
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
$allowed=@('D:\Git PWA\TAKY','D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH','D:\Git PWA\Play Camp','D:\Git PWA\Ready & Set','D:\Git PWA\Hide & Seek','D:\Git PWA\Snap & Pop','D:\Git PWA\TAKY-MOBILE','D:\Git PWA\SAVEY')
if($Repo -notin $allowed -or !(Test-Path -LiteralPath $Repo)){throw 'UNAPPROVED_REPO'}
if([string]::IsNullOrWhiteSpace($Task) -or $Task.Length -gt 2500){throw 'INVALID_TASK'}
# Every future model task must have an existing, explicitly bound portfolio
# work ID. Validation-only local checks do not create AI assignment records.
if($TaskKind -ne 'validation' -and [string]::IsNullOrWhiteSpace($PortfolioTaskId)){
 throw 'PORTFOLIO_WORK_ID_REQUIRED_FOR_MODEL_TASK'
}
if($PortfolioTaskId){
 if($PortfolioTaskId -notmatch '^[A-Za-z0-9-]{3,64}$'){throw 'PORTFOLIO_ID_INVALID'}
 $boardFile='D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\70_EXECUTION_QUEUE\TASK_REGISTER.json'
 $board=Get-Content -LiteralPath $boardFile -Raw -Encoding UTF8|ConvertFrom-Json
 $matching=@($board.tasks|Where-Object {[string]$_.id -ceq $PortfolioTaskId})
 if($matching.Count -ne 1){throw 'PORTFOLIO_ID_NOT_FOUND_OR_DUPLICATE'}
 if($matching[0].status -in @('BLOCKED','REJECTED','VERIFIED')){throw 'PORTFOLIO_TASK_NOT_ACTIVE'}
 if($matching[0].approval_required -eq $true){throw 'PORTFOLIO_NEEDS_SEPARATE_APPROVAL'}
 # The selected WORK_ID must own this registered repository, not merely exist.
 $registry=Get-Content -LiteralPath 'D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL\PROJECT_REGISTRY.json' -Raw -Encoding UTF8|ConvertFrom-Json
 $ownerRepo=if($Repo -eq 'D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH'){'D:\Git PWA\TAKY'}else{$Repo}
 $projects=@($registry.projects.PSObject.Properties|Where-Object {
  [string]::Equals([IO.Path]::GetFullPath(([string]$_.Value.source_repo).Replace('/','\')),[IO.Path]::GetFullPath($ownerRepo),[StringComparison]::OrdinalIgnoreCase)
 })
 if($projects.Count -ne 1){throw 'PORTFOLIO_REPO_OWNER_NOT_REGISTERED'}
 $current=Get-Content -LiteralPath ('D:\Git PWA\TAKY_AI_WORKBENCH\10_PROJECTS\'+$projects[0].Name+'\PROJECT_CURRENT.json') -Raw -Encoding UTF8|ConvertFrom-Json
 if($current.status -eq 'IDLE' -or $registry.projects.($projects[0].Name).status -ne $current.status){throw 'PORTFOLIO_WORK_ID_REPO_SCOPE_MISMATCH'}
 # CURRENT names the primary work, but other tasks in the same project may be
 # active concurrently. They need explicit, registered, in-repo evidence.
 $primary=([string]$current.current_work_id -ceq $PortfolioTaskId)
 $repoPrefix=[IO.Path]::GetFullPath($Repo).TrimEnd('\')+'\'
 # Work IDs exist at INTAKE. A distinct, explicitly registered source
 # binding can authorize later review/edit without becoming implementation
 # completion evidence or borrowing a different CURRENT's source references.
 $plannedRefs=@()
 $plannedBindings=@($matching[0].planned_source_bindings|Where-Object {$null -ne $_})
 if($plannedBindings.Count -gt 0){
  if([string]$matching[0].intake.project -cne [string]$projects[0].Name){throw 'PORTFOLIO_PLANNED_SOURCE_PROJECT_MISMATCH'}
  foreach($binding in $plannedBindings){
   $source=if($binding){[string]$binding.path}else{''}
   if(!$source -or $source -match '\.\.' -or $source -notmatch '^\S' -or
      !([IO.Path]::GetFullPath($source).StartsWith($repoPrefix,[StringComparison]::OrdinalIgnoreCase))){
    throw 'PORTFOLIO_PLANNED_SOURCE_PATH_INVALID'
   }
   if(!(Test-Path -LiteralPath $source -PathType Leaf)){throw 'PORTFOLIO_PLANNED_SOURCE_MISSING'}
   $digest=[Security.Cryptography.SHA256]::Create()
   try{$sourceHash=[BitConverter]::ToString($digest.ComputeHash([IO.File]::ReadAllBytes($source))).Replace('-','').ToLowerInvariant()}
   finally{$digest.Dispose()}
   if($sourceHash -cne [string]$binding.sha256){throw 'PORTFOLIO_PLANNED_SOURCE_CHANGED_REBIND_REQUIRED'}
   $plannedRefs+= $source
  }
 }
 $workRefs=@($matching[0].evidence|Where-Object {$_ -is [string] -and $_.StartsWith($repoPrefix,[StringComparison]::OrdinalIgnoreCase)})
 $workRefs+=@($plannedRefs)
 if(!$primary -and $workRefs.Count -eq 0){throw 'PORTFOLIO_WORK_ID_REPO_SCOPE_MISMATCH'}
 # Task-specific planned refs do not count as user approval or DONE.
 $refs=if($primary){@($matching[0].evidence)+@($current.source_refs)+@($current.output_refs)+@($plannedRefs)}else{@($workRefs)}
 $pattern='(?<![A-Za-z0-9_.-])((?:TAKY2|TOOLS|ENFORCEMENT|DOMAIN|LEARNING|src|app|lib|pages|components|tests)/[A-Za-z0-9_./-]+\.(?:ps1|py|js|cjs|mjs|ts|tsx|jsx|json|css|html|md))\b'
 $named=@([regex]::Matches($Task,$pattern,[Text.RegularExpressions.RegexOptions]::IgnoreCase)|ForEach-Object {$_.Groups[1].Value}|Sort-Object -Unique)
 if($named.Count -eq 0 -and $TaskKind -ne 'implementation'){throw 'PORTFOLIO_TASK_SOURCE_REF_REQUIRED'}
 foreach($rel in $named){
  if($rel.Contains('..')){throw 'PORTFOLIO_TASK_SOURCE_PATH_INVALID'}
  $target=[IO.Path]::GetFullPath((Join-Path $Repo ($rel.Replace('/','\'))))
  $hits=@($refs|Where-Object {$_ -and [string]::Equals([IO.Path]::GetFullPath([string]$_),$target,[StringComparison]::OrdinalIgnoreCase)})
  if($hits.Count -eq 0){throw ('PORTFOLIO_TASK_SOURCE_NOT_OWNED: '+$rel)}
 }
}
# Queue override exists only for isolated local smoke tests; production inbox stays fixed.
$productionQueue='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\01_INBOX\AI_TASKS'
if($QueueRoot -ne $productionQueue){
 $normalized=[IO.Path]::GetFullPath($QueueRoot)
 $testPrefix=[IO.Path]::Combine([IO.Path]::GetFullPath([IO.Path]::GetTempPath()),'TAKY_TASK_')
 if(-not $normalized.StartsWith($testPrefix,[StringComparison]::OrdinalIgnoreCase)){
  throw 'QUEUE_OVERRIDE_OUTSIDE_LOCAL_TEST_ROOT'
 }
}
$usageScript='D:\Git PWA\TAKY\TOOLS\TAKY_USAGE_BOARD.py'
if(!(Test-Path -LiteralPath $usageScript)){throw 'USAGE_MONITOR_MISSING'}
$raw=(& python -X utf8 $usageScript --route-dry-run --task-kind $TaskKind --task-size $TaskSize --planned-calls $PlannedCalls | Out-String)
if($LASTEXITCODE -ne 0){throw 'USAGE_DRYRUN_FAILED'}
try{$route=$raw | ConvertFrom-Json}catch{throw 'USAGE_DRYRUN_BAD_JSON'}
if($route.dryRun -ne $true -or $route.inferenceCalls -ne 0 -or $route.paidApiCalls -ne 0){throw 'USAGE_GATE_UNVERIFIED'}
if($TaskKind -eq 'validation'){
 if($route.status -ne 'READY_LOCAL_ONLY'){throw 'LOCAL_VALIDATION_GATE_UNAVAILABLE'}
 @{status='LOCAL_ONLY_NO_MODEL_TASK';route=$route} | ConvertTo-Json -Depth 10
 exit 0
}
if($route.status -ne 'READY_FOR_SEPARATE_AUTHORIZATION'){throw ('USAGE_GATE_HOLD: '+[string]$route.status)}
# Quota SAFE is not an authorization to run. Consult the signed TAKY2
# route ledger *without creating a preflight receipt* before preparing a task.
$primary=if($route.recommended -eq 'Codex CLI'){'Codex'}elseif($route.recommended -eq 'Claude Code'){'Claude'}else{''}
$candidateOrder=if($Executor -eq 'Auto'){@($primary, $(if($primary -eq 'Codex'){'Claude'}else{'Codex'}))}else{@($Executor)}
$chosen=$null
$governed=$null
$routeReasons=@()
$routeHealth='D:\Git PWA\TAKY\TOOLS\TAKY_GOVERNED_ROUTE_HEALTH.py'
if(!(Test-Path -LiteralPath $routeHealth)){throw 'TAKY_GOVERNANCE_CHECK_MISSING'}
foreach($entry in $candidateOrder){
 if(!$entry){continue}
 $providerName=if($entry -eq 'Codex'){'Codex CLI'}else{'Claude Code'}
 $safe=@($route.candidates|Where-Object {$_.provider -eq $providerName -and $_.risk -eq 'SAFE'})
 if($safe.Count -ne 1){$routeReasons+=($entry+':QUOTA_NOT_SAFE');continue}
 $healthRaw=(& python -X utf8 $routeHealth --executor $entry --repo $Repo | Out-String)
 if($LASTEXITCODE -ne 0){throw 'TAKY_GOVERNANCE_READBACK_UNAVAILABLE'}
 try{$health=$healthRaw|ConvertFrom-Json}catch{throw 'TAKY_GOVERNANCE_READBACK_INVALID'}
 if($health.status -eq 'READY_FOR_EXISTING_COST_AND_APPROVAL_GATES'){$chosen=$entry;$governed=$health;break}
 $routeReasons+=($entry+':'+[string]$health.reason)
}
if(!$chosen){throw ('TAKY_GOVERNANCE_ROUTE_HOLD: '+($routeReasons -join ','))}
$route|Add-Member -NotePropertyName governedRouteHealth -NotePropertyValue $governed -Force
$scope=@()
if($TaskKind -eq 'implementation'){
 if($AllowedFiles.Count -lt 1 -or !$AcceptanceCriteria.Trim()){throw 'EDIT_SCOPE_REQUIRED'}
 if(($Task.Length + $AcceptanceCriteria.Length + ($AllowedFiles -join ',').Length) -gt 1600){throw 'EDIT_PACKET_PROMPT_TOO_LONG'}
 foreach($name in $AllowedFiles){
  if($name -notmatch '^[A-Za-z0-9_./-]+$' -or $name.Contains('..') -or $name.StartsWith('/')){throw 'UNSAFE_EDIT_PATH'}
  $file=Join-Path $Repo ($name -replace '/','\')
  if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw 'EDIT_FILE_MISSING'}
  if((Get-Item -LiteralPath $file).Length -gt 100000){throw 'EDIT_FILE_TOO_LARGE'}
  # Implementation files require the same registered work ownership as review sources.
  $target=[IO.Path]::GetFullPath($file)
  $evidence=@($refs|Where-Object {$_ -and [string]::Equals([IO.Path]::GetFullPath([string]$_),$target,[StringComparison]::OrdinalIgnoreCase)})
  if($evidence.Count -eq 0){throw ('PORTFOLIO_EDIT_SOURCE_NOT_OWNED: '+$name)}
  $scope+=@{path=$name;sha256=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()}
 }
 $uniqueNames=@($scope|ForEach-Object {$_['path']}|Select-Object -Unique)
 if($uniqueNames.Count -ne $scope.Count){throw 'DUPLICATE_EDIT_FILE'}
}elseif($AllowedFiles.Count -gt 0){throw 'REVIEW_CANNOT_EDIT'}
$branch=git -C $Repo branch --show-current
$head=git -C $Repo rev-parse HEAD
if($LASTEXITCODE -ne 0 -or !$head){throw 'GIT_NOT_READY'}
$prepareMutex=[System.Threading.Mutex]::new($false,'Local\TAKY_CHAT_PREP_SINGLETON')
$prepareLock=$false
try {
 $prepareLock=$prepareMutex.WaitOne(5000)
 if(-not $prepareLock){throw 'TASK_PREP_LOCK_BUSY'}
# A preparation request is not execution evidence. Reuse only an identical
# recent, unexecuted request. Do not treat completed/failed/stale work as reusable.
$existingMatch=$null
if(Test-Path -LiteralPath $QueueRoot){
 foreach($entry in @(Get-ChildItem -LiteralPath $QueueRoot -Filter '*.json' -File -ErrorAction Stop | Select-Object -First 300)){
  try {
   $prior=Get-Content -LiteralPath $entry.FullName -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
   if($prior.schema -ne 'TAKY_EXECUTION_REQUEST_V1' -or $prior.state -ne 'PREPARED_NOT_EXECUTED'){continue}
   if([string]$prior.id -notmatch '^[0-9a-f]{32}$'){continue}
   # A prepared request already bearing a dispatch receipt may have failed or
   # timed out. Never silently reuse it just because its queue state is stale.
   $receiptPath=Join-Path 'F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY' ('TAKY_ROUTED_'+$prior.id+'.json')
   if(Test-Path -LiteralPath $receiptPath){continue}
   $age=([DateTime]::UtcNow-[DateTime]::Parse([string]$prior.created_utc).ToUniversalTime()).TotalMinutes
   if($age -lt 0 -or $age -gt 10){continue}
   if($prior.executor -ne $chosen -or $prior.repo -ne $Repo -or $prior.branch -ne $branch -or $prior.head -ne $head){continue}
   if([string]$prior.portfolio_task_id -cne $PortfolioTaskId){continue}
   if(-not [string]::Equals([string]$prior.task,$Task,[StringComparison]::Ordinal)){continue}
   if($prior.task_kind -ne $TaskKind -or $prior.task_size -ne $TaskSize -or $prior.planned_calls -ne $PlannedCalls){continue}
   if($TaskKind -eq 'implementation'){
    if($prior.acceptance_criteria -cne $AcceptanceCriteria -or
       (ConvertTo-Json -Compress @($prior.allowed_files)) -cne (ConvertTo-Json -Compress @($scope))){continue}
   }
   $existingMatch=$prior;break
  } catch {continue}
 }
}
if($DryRun) {
 @{schema='TAKY_EXECUTION_PREP_DRYRUN_V1';status='READY_FOR_SEPARATE_AUTHORIZATION'
   selectedExecutor=$chosen;taskKind=$TaskKind;taskSize=$TaskSize;repo=$Repo
   noModelCalled=$true;noRemoteWrite=$true;wouldReusePreparedRequest=($null -ne $existingMatch)
   allowedFiles=$scope;portfolioTaskId=$PortfolioTaskId;route=$route} | ConvertTo-Json -Depth 12
 exit 0
}
if($null -ne $existingMatch){
 @{schema='TAKY_EXECUTION_PREP_REUSE_V1';status='REUSED_PREPARED_NOT_EXECUTED'
   task_file=$existingMatch.task_file;id=$existingMatch.id
   noModelCalled=$true;noRemoteWrite=$true;route=$route} | ConvertTo-Json -Depth 12
 exit 0
}
$dir=$QueueRoot
[IO.Directory]::CreateDirectory($dir)|Out-Null
$id=[guid]::NewGuid().ToString('N')
$obj=[ordered]@{
 schema='TAKY_EXECUTION_REQUEST_V1';id=$id;state='PREPARED_NOT_EXECUTED'
 executor=$chosen;repo=$Repo;branch=$branch;head=$head
 task=$Task;context_policy='TARGETED_FILES_ONLY';resume_large_session=$false
 max_turns=1;approval='REQUIRED_BEFORE_MODEL_CALL'
 mode=if($TaskKind -eq 'implementation'){'BOUNDED_EDIT_PROPOSAL'}else{'READ_ONLY_REVIEW'}
 allowed_files=$scope;acceptance_criteria=$AcceptanceCriteria;portfolio_task_id=$PortfolioTaskId
 task_kind=$TaskKind;task_size=$TaskSize;planned_calls=$PlannedCalls
 route_selection=if($Executor -eq 'Auto'){'AUTO'}else{'EXPLICIT'}
 route_preflight=$route;no_push=$true;no_deploy=$true
 created_utc=[DateTime]::UtcNow.ToString('o')
}
$file=Join-Path $dir "$id.json"
$obj['task_file']=$file
[IO.File]::WriteAllText($file,($obj|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$obj|ConvertTo-Json -Depth 12
} finally {
 if($prepareLock){$prepareMutex.ReleaseMutex()|Out-Null}
 $prepareMutex.Dispose()
}