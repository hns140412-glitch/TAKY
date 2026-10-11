param([switch]$Publish)
$ErrorActionPreference='Stop'
$root='F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON'
$claude=Join-Path $env:USERPROFILE '.claude\projects\D--Git-PWA-TAKY-2-0-ORCH'
$codex=Join-Path $env:USERPROFILE '.codex\sessions'
$lastClaude=Get-ChildItem -LiteralPath $claude -Filter '*.jsonl' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
$lastCodex=Get-ChildItem -LiteralPath $codex -Filter '*.jsonl' -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
$state=[ordered]@{
 schema='TAKY_WORK_CONTEXT_STATUS_V1'
 derived_not_authority=$true
 captured_utc=(Get-Date).ToUniversalTime().ToString('o')
 antigravity_window=@(Get-Process 'Antigravity IDE' -ErrorAction SilentlyContinue | Where-Object MainWindowHandle -ne 0 | Select-Object Id,MainWindowTitle)
 claude=[ordered]@{latest_session_id=$lastClaude.BaseName;updated_utc=if($lastClaude){$lastClaude.LastWriteTimeUtc.ToString('o')}else{$null};panel_binding='UNVERIFIED'}
 codex=[ordered]@{latest_session_file=if($lastCodex){$lastCodex.Name}else{$null};updated_utc=if($lastCodex){$lastCodex.LastWriteTimeUtc.ToString('o')}else{$null};antigravity_binding='UNVERIFIED'}
 drive=[ordered]@{folder_present=(Test-Path $root);cloud_readback='PARTIAL'}
 bridge=[ordered]@{inspect='PASS';panel_input='UNVERIFIED';panel_response='UNVERIFIED';auto_capture='OPEN'}
}
$json=$state|ConvertTo-Json -Depth 10
if($Publish){
 $dest=Join-Path $root '02_CURRENT\TAKY_WORK_CONTEXT_STATUS.json'
 [System.IO.File]::WriteAllText($dest,$json,[System.Text.UTF8Encoding]::new($false))
 Write-Output "PUBLISHED=$dest"
}
Write-Output $json
