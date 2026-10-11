param([string]$Project='D--Git-PWA-TAKY-2-0-ORCH',[string]$SessionId,[switch]$Publish)
$ErrorActionPreference='Stop'
$folder=Join-Path $env:USERPROFILE ".claude\projects\$Project"
$files=@(Get-ChildItem -LiteralPath $folder -Filter '*.jsonl' -File | Sort-Object LastWriteTimeUtc -Descending)
if(!$SessionId){$file=$files | Select-Object -First 1}else{$file=$files | Where-Object BaseName -eq $SessionId | Select-Object -First 1}
if(!$file){throw 'No matching session'}
$types=@{};$last='';$valid=0
foreach($line in [System.IO.File]::ReadLines($file.FullName)){
 try {$j=$line|ConvertFrom-Json -ErrorAction Stop; $valid++; $t=[string]$j.type;if(!$types.ContainsKey($t)){$types[$t]=0};$types[$t]++;if($j.timestamp){$last=[string]$j.timestamp}}catch{}
}
$receipt=[ordered]@{status='METADATA_ONLY';project=$Project;session_id=$file.BaseName;path=$file.FullName;size_bytes=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o');last_event_timestamp=$last;valid_jsonl_lines=$valid;types=$types;panel_session_identity='UNVERIFIED';prompt_response_content='NOT_EXPORTED'}
$json=$receipt|ConvertTo-Json -Depth 8
if($Publish){
 $dest='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY'
 if(!(Test-Path $dest)){throw 'Drive history path missing'}
 $output=Join-Path $dest ('CLAUDE_SESSION_RECEIPT_'+$file.BaseName+'.json')
 [System.IO.File]::WriteAllText($output,$json,[System.Text.UTF8Encoding]::new($false))
 Write-Output "PUBLISHED=$output"
}
Write-Output $json
