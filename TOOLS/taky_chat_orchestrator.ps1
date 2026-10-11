param(
 [ValidateSet('Status','GitStatus','LocalRepoInfo','LocalVerify','Dispatch')][string]$Action='Status',
 [string]$Repo='D:\Git PWA\TAKY',
 [ValidateSet('Claude','Codex')][string]$Executor='Claude',
 [string]$Task='',
 [switch]$AuthorizeModelCall
)
$ErrorActionPreference='Stop'
$repos=@('D:\Git PWA\TAKY','D:\Git PWA\TAKY-2.0-ORCH','D:\Git PWA\Play Camp','D:\Git PWA\Ready-Set','D:\Git PWA\Hide-Seek','D:\Git PWA\Snap-Pop','D:\Git PWA\SAVEY')
if($Repo -notin $repos){throw 'Repository not allowlisted'}
if(!(Test-Path -LiteralPath $Repo)){throw 'Repository path unavailable'}
$root='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON'
$history=Join-Path $root '04_HISTORY'
[System.IO.Directory]::CreateDirectory($history)|Out-Null
$id=[guid]::NewGuid().ToString('N')
$start=[DateTime]::UtcNow.ToString('o')
$result=[ordered]@{schema='TAKY_CHAT_ORCH_V1';id=$id;action=$Action;repo=$Repo;executor=$null;started_utc=$start;status='STARTED';model_called=$false;output=''}
try {
 switch($Action){
  'Status' {
   $result.output="PC orchestration online; model dispatch requires explicit authorization; Git and Drive paths independent of native Antigravity panel."
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
  'Dispatch' {
   if([string]::IsNullOrWhiteSpace($Task)){throw 'Task required'}
   if(!$AuthorizeModelCall){throw 'HOLD: model use requires -AuthorizeModelCall and TAKY approval'}
   if($env:TAKY_USER_EXPLICIT_AUTHORIZATION -ne '1'){throw 'HOLD: user authorization environment absent'}
   throw 'HOLD: do not invoke model until session continuity and executor receipt gates are wired and verified'
  }
 }
 $result.status='PASS'
} catch {
 $result.status='HOLD'
 $result.output=$_.Exception.Message
}
$result.finished_utc=[DateTime]::UtcNow.ToString('o')
$path=Join-Path $history "TAKY_CHAT_ORCH_$id.json"
[System.IO.File]::WriteAllText($path,($result|ConvertTo-Json -Depth 6),[System.Text.UTF8Encoding]::new($false))
$result | ConvertTo-Json -Depth 6
