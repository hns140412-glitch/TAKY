param([string]$Project='D--Git-PWA-TAKY-2-0-ORCH',[int]$Limit=8)
$ErrorActionPreference='Stop'
$folder=Join-Path $env:USERPROFILE ".claude\projects\$Project"
if(-not (Test-Path -LiteralPath $folder)){throw "No Claude project session directory"}
Get-ChildItem -LiteralPath $folder -Filter '*.jsonl' -File |
 Sort-Object LastWriteTimeUtc -Descending |
 Select-Object -First $Limit |
 ForEach-Object {
  [pscustomobject]@{session_id=$_.BaseName;updated_utc=$_.LastWriteTimeUtc.ToString('o');bytes=$_.Length;path=$_.FullName}
 } | ConvertTo-Json -Depth 4
