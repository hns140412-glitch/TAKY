# Synthetic local contract check, Windows runner only. No Notion login, real tasks or user data.
$ErrorActionPreference = 'Stop'
$base=Join-Path $env:TEMP ('TAKY-NOTION-SYNTH-'+[guid]::NewGuid().ToString('N'))
$vault=Join-Path $base 'SOURCE-VAULT'
$reports=Join-Path $vault 'reports'
$output=Join-Path $base 'outside-reports'
New-Item -Path $reports -ItemType Directory -Force | Out-Null
$queue=@(
    [ordered]@{notion_page_id='fake-a';kind='NEW';mining_status='PENDING_NOT_PROMOTED'},
    [ordered]@{notion_page_id='fake-b';kind='BASELINE_FIRST_OBSERVATION';mining_status='PENDING_NOT_PROMOTED'}
)
$summary=[ordered]@{
    time='2026-09-28T02:15:46Z';notion_total=2;queue_count=2;new_vs_baseline=1;
    baseline=1;block_errors=0;mining_promotion='NOT_CONNECTED'
}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $reports 'INCREMENTAL_SUMMARY.json') -Encoding UTF8
$queue | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $reports 'INCREMENTAL_QUEUE.json') -Encoding UTF8
'[]' | Set-Content -LiteralPath (Join-Path $reports 'INCREMENTAL_ERRORS.json') -Encoding UTF8
'{"schema":"synthetic_handoff_only"}' | Set-Content -LiteralPath (Join-Path $reports 'MINING_INBOX_HANDOFF.json') -Encoding UTF8
$files=@(Get-ChildItem -LiteralPath $reports -File)
$before=@{};foreach($file in $files){$before[$file.Name]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
$scriptPath=Join-Path $PSScriptRoot 'TAKY-NOTION-STATUS.ps1'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath -VaultRoot $vault -ExpectedNotionCount 2 -OutputRoot $output
if ($LASTEXITCODE -ne 0) {
    $debug=@(Get-ChildItem -LiteralPath $output -Recurse -Filter NOTION_STATUS.json -File | Select-Object -First 1)
    if ($debug.Count) {
        $x=Get-Content -LiteralPath $debug[0].FullName -Raw | ConvertFrom-Json
        Write-Host ('SYNTH_DEBUG_STATUS='+$x.status+' ISSUES='+(@($x.issues) -join ',')+
          ' COUNTS='+($x.counts | ConvertTo-Json -Compress -Depth 3))
    }
    throw 'SYNTH_CURRENT_MATCH_SHOULD_PASS'
}
$receipts=@(Get-ChildItem -LiteralPath $output -Recurse -Filter NOTION_STATUS.json -File)
if ($receipts.Count -ne 1) { throw 'SYNTH_MISSING_PASS_RECEIPT' }
$pass=Get-Content -LiteralPath $receipts[0].FullName -Raw | ConvertFrom-Json
if ($pass.status -ne 'COUNT_MATCHES_SUPPLIED_SNAPSHOT_IDS_UNVERIFIED' -or $pass.counts.queueRows -ne 2 -or $pass.counts.distinctPageIds -ne 2) {
    throw 'SYNTH_PASS_RECEIPT_MISMATCH'
}
if ($pass.fullCurrentPageIdentityVerified -or $pass.driveSyncVerified -or $pass.semanticMiningExecuted) {
    throw 'SYNTH_FALSE_VERIFICATION_CLAIM'
}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath -VaultRoot $vault -ExpectedNotionCount 3 -OutputRoot $output
if ($LASTEXITCODE -ne 2) { throw 'SYNTH_STALE_QUEUE_SHOULD_HOLD' }
$receipts=@(Get-ChildItem -LiteralPath $output -Recurse -Filter NOTION_STATUS.json -File)
if ($receipts.Count -ne 2) { throw 'SYNTH_MISSING_HOLD_RECEIPT' }
$hold=@($receipts | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } | Where-Object { $_.status -eq 'HOLD_LOCAL_OR_FRESHNESS_GAP' })
if ($hold.Count -ne 1 -or @($hold[0].issues) -notcontains 'CURRENT_NOTION_COUNT_DIFFERS_FROM_LOCAL_SUMMARY') {
    throw 'SYNTH_STALE_NOT_DETECTED'
}
foreach($file in $files){if($before[$file.Name] -ne (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash){throw 'SYNTH_SOURCE_MUTATED'}}
$reportTexts=($receipts | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }) -join ' '
if ($reportTexts -match 'fake-a|fake-b') { throw 'SYNTH_PRIVATE_SOURCE_ID_LEAK' }
Write-Host 'PASS: synthetic Notion PowerShell status receipts; current match, stale HOLD, no input writes or source-ID leakage.'
