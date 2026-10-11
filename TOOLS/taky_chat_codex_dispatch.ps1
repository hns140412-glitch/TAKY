param(
 [Parameter(Mandatory=$true)][string]$TaskFile,
 [switch]$Execute
)
$ErrorActionPreference='Stop'
$task=Get-Content -LiteralPath $TaskFile -Raw -Encoding UTF8 | ConvertFrom-Json
if($task.schema -ne 'TAKY_EXECUTION_REQUEST_V1' -or $task.executor -ne 'Codex'){throw 'WRONG_TASK'}
if($task.state -ne 'PREPARED_NOT_EXECUTED'){throw 'INVALID_STATE'}
$allow=@('D:\Git PWA\TAKY','D:\Git PWA\TAKY-2.0-ORCH','D:\Git PWA\Play Camp')
if($task.repo -notin $allow){throw 'REPO_NOT_ALLOWED'}
if(!(Test-Path -LiteralPath $task.repo)){throw 'MISSING_REPO'}
$current=(git -C $task.repo rev-parse HEAD)
if($LASTEXITCODE -ne 0 -or $current -ne $task.head){throw 'HEAD_CHANGED_REPREPARE'}
if(!$Execute){'READY_NO_MODEL_CALL';exit 0}
if($env:TAKY_USER_EXPLICIT_AUTHORIZATION -ne '1'){throw 'EXPLICIT_AUTHORIZATION_REQUIRED'}
$shim='D:\Git PWA\TAKY\TOOLS\TAKY_CODEX_SHIM.ps1'
$real='C:\Users\YKH_1507-03\AppData\Roaming\npm\codex.cmd'
if(!(Test-Path -LiteralPath $shim) -or !(Test-Path -LiteralPath $real)){throw 'CODEX_INSTALL_MISSING'}
$receiptDir='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY'
$receipt=Join-Path $receiptDir ("CODEX_CHAT_"+$task.id+".json")
$env:TAKY_USER_INTENT=[string]$task.task
$details=[ordered]@{id=$task.id;executor='Codex';status='STARTED';created_utc=[DateTime]::UtcNow.ToString('o');repo=$task.repo;result='';exit_code=$null}
try {
 Push-Location $task.repo
 $argsList=@('exec','--cd',[string]$task.repo,'--sandbox','read-only','--json',[string]$task.task)
 $output=(& $shim @argsList 2>&1 | Out-String)
 $exitCode=$LASTEXITCODE
 $details.result=$output.Substring(0,[Math]::Min($output.Length,20000))
 $details.exit_code=$exitCode
 $details.status=if($exitCode -eq 0){'COMPLETE_UNVERIFIED'}else{'FAILED'}
} catch { $details.status='ERROR';$details.result=$_.Exception.Message }
finally {
 Pop-Location
 $details.finished_utc=[DateTime]::UtcNow.ToString('o')
 [IO.File]::WriteAllText($receipt,($details|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
}
$details|ConvertTo-Json -Depth 6
