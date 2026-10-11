param([int]$PollSeconds=3,[int]$MaxCycles=0)
$ErrorActionPreference='Stop'
if($PollSeconds -lt 2 -or $PollSeconds -gt 60){throw 'PollSeconds must be 2..60'}
$engine=Join-Path $PSScriptRoot 'taky_headless_mailbox.ps1'
$logRoot=Join-Path $env:LOCALAPPDATA 'TAKY\bridge'
[System.IO.Directory]::CreateDirectory($logRoot)|Out-Null
$lockFile=Join-Path $logRoot 'worker.lock'
$lock=$null
try {$lock=[System.IO.FileStream]::new($lockFile,[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)}
catch {throw 'WORKER_ALREADY_RUNNING'}
try {
 $cycle=0
 do {
   & $engine -Mode WorkerOnce
   if(!$?){throw 'WORKER_ONCE_FAILED'}
   $cycle++
   if($MaxCycles -gt 0 -and $cycle -ge $MaxCycles){break}
   Start-Sleep -Seconds $PollSeconds
 } while($true)
} finally {$lock.Dispose()}
