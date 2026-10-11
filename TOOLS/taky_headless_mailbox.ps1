param(
 [ValidateSet('Init','Send','Poll','WorkerOnce')][string]$Mode='Init',
 [string]$Message='',
 [string]$Id='',
 [ValidateSet('ECHO_TEST_ONLY','LOCAL_REPO_INFO','GIT_STATUS','LOCAL_VERIFY','CLAUDE','CODEX')][string]$Executor='ECHO_TEST_ONLY',
 [string]$Repo='D:\Git PWA\TAKY',
 [string]$Root='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\01_INBOX\TAKY_BRIDGE'
)
$ErrorActionPreference='Stop'
$allowedRepos=@('D:\Git PWA\TAKY','D:\Git PWA\TAKY-2.0-ORCH','D:\Git PWA\Play Camp','D:\Git PWA\Ready-Set','D:\Git PWA\Hide-Seek','D:\Git PWA\Snap-Pop','D:\Git PWA\SAVEY')
function SaveJson($path,$obj){
 $temp="$path.tmp.$PID"
 [IO.File]::WriteAllText($temp,($obj|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 Move-Item -LiteralPath $temp -Destination $path -Force
}
if($Mode -eq 'Init'){
 foreach($part in @('requests','responses','processed')){[IO.Directory]::CreateDirectory((Join-Path $Root $part))|Out-Null}
 "MAILBOX_READY=$Root";exit
}
if(!(Test-Path -LiteralPath (Join-Path $Root 'requests'))){throw 'Run Init first'}
if($Mode -eq 'Send'){
 if($Repo -notin $allowedRepos){throw 'Repo not allowlisted'}
 if($Message.Length -gt 2000){throw 'Message too long'}
 if($Executor -eq 'ECHO_TEST_ONLY' -and [string]::IsNullOrWhiteSpace($Message)){throw 'Message required'}
 $id=[guid]::NewGuid().ToString('N')
 $obj=[ordered]@{schema='TAKY_BRIDGE_V2';id=$id;created_utc=[DateTime]::UtcNow.ToString('o');executor=$Executor;repo=$Repo;message=$Message}
 SaveJson (Join-Path $Root "requests\$id.json") $obj
 "SENT_ID=$id";exit
}
if($Mode -eq 'WorkerOnce'){
 foreach($f in @(Get-ChildItem (Join-Path $Root 'requests') -File -Filter '*.json')){
  $dest=Join-Path $Root "processed\$($f.Name)"
  if(Test-Path -LiteralPath $dest){continue}
  $obj=Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8|ConvertFrom-Json
  $status='HOLD';$output='Unsupported operation';$repoPath=[string]$obj.repo
  try {
   if($obj.executor -eq 'ECHO_TEST_ONLY'){
    $status='ECHO_PASS';$output="ACK: $($obj.message)"
   } elseif($obj.executor -in @('CLAUDE','CODEX')){
    $status='HOLD';$output='No AI invocation: session-bound executor and approval gate not verified'
   } elseif($obj.executor -in @('LOCAL_REPO_INFO','GIT_STATUS','LOCAL_VERIFY')){
    if($repoPath -notin $allowedRepos -or !(Test-Path -LiteralPath $repoPath)){throw 'Repository not authorized or missing'}
    if($obj.executor -eq 'LOCAL_VERIFY'){
     $verifyScript=Join-Path $PSScriptRoot 'taky_chat_orchestrator.ps1'
     $verifyText=(& $verifyScript -Action LocalVerify -Repo $repoPath | Out-String)
     $verify=$verifyText|ConvertFrom-Json
     $status=[string]$verify.status
     $output=[string]$verify.output
    } elseif($obj.executor -eq 'LOCAL_REPO_INFO'){
     $h=(git -C $repoPath rev-parse HEAD)
     if($LASTEXITCODE -ne 0){throw 'git HEAD failed'}
     $b=(git -C $repoPath branch --show-current)
     $output="HEAD=$h BRANCH=$b";$status='PASS'
    } else {
     $output=((git -C $repoPath status --short --untracked-files=no | Select-Object -First 60) -join "`n")
     if($LASTEXITCODE -ne 0){throw 'git status failed'}
     $status='PASS'
    }
   }
  } catch {$status='ERROR';$output=$_.Exception.Message}
  $reply=[ordered]@{schema='TAKY_BRIDGE_V2';id=$obj.id;executor=$obj.executor;status=$status;response=$output;processed_utc=[DateTime]::UtcNow.ToString('o');ai_called=$false}
  SaveJson (Join-Path $Root "responses\$($obj.id).json") $reply
  Copy-Item -LiteralPath $f.FullName -Destination $dest -ErrorAction Stop
  "PROCESSED_ID=$($obj.id);STATUS=$status"
 }
 exit
}
if($Mode -eq 'Poll'){
 if($Id -notmatch '^[0-9a-f]{32}$'){throw 'Invalid id'}
 $file=Join-Path $Root "responses\$Id.json"
 if(!(Test-Path -LiteralPath $file)){'PENDING';exit}
 Get-Content -LiteralPath $file -Raw -Encoding UTF8
}
