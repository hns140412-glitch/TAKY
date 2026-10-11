param(
 [Parameter(Mandatory=$true)][string]$Task,
 [ValidateSet('Claude','Codex')][string]$Executor='Claude',
 [string]$Repo='D:\Git PWA\TAKY'
)
$ErrorActionPreference='Stop'
$allowed=@('D:\Git PWA\TAKY','D:\Git PWA\TAKY-2.0-ORCH','D:\Git PWA\Play Camp','D:\Git PWA\Ready-Set','D:\Git PWA\Hide-Seek','D:\Git PWA\Snap-Pop','D:\Git PWA\SAVEY')
if($Repo -notin $allowed -or !(Test-Path -LiteralPath $Repo)){throw 'UNAPPROVED_REPO'}
if([string]::IsNullOrWhiteSpace($Task) -or $Task.Length -gt 2500){throw 'INVALID_TASK'}
$branch=git -C $Repo branch --show-current
$head=git -C $Repo rev-parse HEAD
if($LASTEXITCODE -ne 0){throw 'GIT_NOT_READY'}
$dir='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\01_INBOX\AI_TASKS'
[IO.Directory]::CreateDirectory($dir)|Out-Null
$id=[guid]::NewGuid().ToString('N')
$obj=[ordered]@{
 schema='TAKY_EXECUTION_REQUEST_V1';id=$id;state='PREPARED_NOT_EXECUTED'
 executor=$Executor;repo=$Repo;branch=$branch;head=$head
 task=$Task;context_policy='TARGETED_FILES_ONLY';resume_large_session=$false
 max_turns=1;approval='REQUIRED_BEFORE_MODEL_CALL';mode='READ_ONLY_REVIEW'
 no_push=$true;no_deploy=$true;created_utc=[DateTime]::UtcNow.ToString('o')
}
$file=Join-Path $dir "$id.json"
[IO.File]::WriteAllText($file,($obj|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
$obj|ConvertTo-Json -Depth 7
