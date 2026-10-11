param(
 [Parameter(Mandatory=$true)][string]$EventJsonPath,
 [string]$DriveRoot = 'F:\내 드라이브\TAKY'
)
$ErrorActionPreference='Stop'
$event = Get-Content -LiteralPath $EventJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$required=@('event_id','session_id','captured_at','actor','project_namespace','intent','action','outcome','provenance')
foreach($key in $required) { if(-not $event.PSObject.Properties[$key] -or [string]::IsNullOrWhiteSpace([string]$event.$key)) { throw "Missing required field: $key" } }
$valid=@('PLANNED','IN_PROGRESS','VERIFIED','BLOCKED','UNKNOWN','SUPERSEDED')
if($event.PSObject.Properties['status'] -and $event.status -notin $valid) { throw "Invalid status: $($event.status)" }
$history=Join-Path $DriveRoot '20_PLATFORM\03_COMMON\04_HISTORY'
if(-not (Test-Path -LiteralPath $history -PathType Container)){ throw "Existing Drive history folder not found: $history" }
$filename='TAKY_CONVERSATION_EVENTS_'+([string]$event.session_id -replace '[^A-Za-z0-9_-]','_')+'.jsonl'
$target=Join-Path $history $filename
$line=$event | ConvertTo-Json -Depth 20 -Compress
$bytes=[System.Text.UTF8Encoding]::new($false).GetBytes($line+[Environment]::NewLine)
$stream=[System.IO.FileStream]::new($target,[System.IO.FileMode]::Append,[System.IO.FileAccess]::Write,[System.IO.FileShare]::Read)
try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush() } finally { $stream.Dispose() }
Write-Output "EVENT_APPENDED=$target"
Write-Output "EVENT_ID=$($event.event_id)"
