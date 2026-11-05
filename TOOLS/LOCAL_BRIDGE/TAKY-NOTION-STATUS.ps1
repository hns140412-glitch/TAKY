# TAKY NOTION local receipt/status check v0.1. Windows PowerShell 5.1+, READ ONLY.
# Does NOT query Notion, execute START_INCREMENTAL.bat, acknowledge queue, or sync Drive.
# Existing SOURCE VAULT files are inputs; small aggregate receipts go to Documents only.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$VaultRoot,
    [int]$ExpectedNotionCount = 0,
    [string]$TaskName = '',
    [string]$TaskPath = '\',
    [string]$OutputRoot = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'TAKY-PC-Reports')
)
$ErrorActionPreference = 'Stop'
if ($ExpectedNotionCount -lt 0) { throw 'ExpectedNotionCount must be >= 0 (0 means not independently supplied).' }
$root = [System.IO.Path]::GetFullPath($VaultRoot).TrimEnd('\','/')
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'VAULT_ROOT_NOT_FOUND' }
$outFull = [System.IO.Path]::GetFullPath($OutputRoot).TrimEnd('\','/')
if ($outFull.Equals($root,[System.StringComparison]::OrdinalIgnoreCase) -or
    $outFull.StartsWith(($root + '\'),[System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'REPORT_OUTPUT_INSIDE_SOURCE_VAULT_FORBIDDEN'
}
$reports = Join-Path $root 'reports'
$issues = New-Object 'System.Collections.Generic.List[string]'
$results = [ordered]@{
    schema='TAKY_NOTION_PC_READ_ONLY_STATUS_V1'
    generated=(Get-Date).ToString('o')
    scope='EXISTING_SOURCE_VAULT_AGGREGATE_METADATA_ONLY'
    liveNotionQueried=$false
    expectedCurrentNotionCount=if ($ExpectedNotionCount -gt 0) {$ExpectedNotionCount} else {$null}
    expectedCountAuthority='EXTERNALLY_OBSERVED_INPUT_NOT_VERIFIED_BY_THIS_SCRIPT'
    files=[ordered]@{}
    counts=[ordered]@{}
    windowsTask=[ordered]@{ taskChecked=$false; lastRunTime=$null; nextRunTime=$null; lastTaskResult=$null; state='NOT_REQUESTED' }
    queueAcknowledged=$false
    semanticMiningExecuted=$false
    indexingExecuted=$false
    driveSyncVerified=$false
    fullCurrentPageIdentityVerified=$false
    status='NOT_VERIFIED'
}
$rawByName=@{}
foreach ($name in @('INCREMENTAL_SUMMARY.json','INCREMENTAL_QUEUE.json','INCREMENTAL_ERRORS.json','MINING_INBOX_HANDOFF.json')) {
    $path=Join-Path $reports $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        [void]$issues.Add('MISSING_'+$name.Replace('.json',''))
        $results.files[$name]=[ordered]@{exists=$false}
        continue
    }
    try {
        $rawByName[$name]=Get-Content -LiteralPath $path -Raw -Encoding UTF8
        [void](ConvertFrom-Json -InputObject $rawByName[$name] -ErrorAction Stop)
        $item=Get-Item -LiteralPath $path
        $results.files[$name]=[ordered]@{
            exists=$true; validJson=$true; sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
            lastWriteTimeUtc=$item.LastWriteTimeUtc.ToString('o'); bytes=$item.Length
        }
    } catch {
        [void]$issues.Add('INVALID_JSON_'+$name.Replace('.json',''))
        $results.files[$name]=[ordered]@{exists=$true;validJson=$false}
    }
}
if ($rawByName.ContainsKey('INCREMENTAL_SUMMARY.json') -and $rawByName.ContainsKey('INCREMENTAL_QUEUE.json')) {
    try {
        $summary=ConvertFrom-Json -InputObject $rawByName['INCREMENTAL_SUMMARY.json']
        # Windows PowerShell 5.1 can emit a JSON array as ONE pipeline value;
        # wrapping ConvertFrom-Json in @() counts its container, not its rows.
        $parsedQueue=ConvertFrom-Json -InputObject $rawByName['INCREMENTAL_QUEUE.json']
        if (-not ($parsedQueue -is [array])) { throw 'QUEUE_JSON_NOT_ARRAY' }
        [object[]]$queue=$parsedQueue
        $ids=@($queue | ForEach-Object { [string]$_.notion_page_id })
        $unique=@($ids | Where-Object { $_ -and $_.Trim() } | Sort-Object -Unique)
        $new=@($queue | Where-Object { $_.kind -eq 'NEW' })
        $baseline=@($queue | Where-Object { $_.kind -eq 'BASELINE_FIRST_OBSERVATION' })
        $pending=@($queue | Where-Object { $_.mining_status -eq 'PENDING_NOT_PROMOTED' })
        $results.counts = [ordered]@{
            summaryNotionTotal=[int]$summary.notion_total
            summaryQueueCount=[int]$summary.queue_count
            queueRows=$queue.Count
            distinctPageIds=$unique.Count
            newRows=$new.Count; baselineRows=$baseline.Count; pendingRows=$pending.Count
            reportedBlockErrors=[int]$summary.block_errors
            summaryTimestamp=$summary.time
        }
        if ($queue.Count -ne [int]$summary.queue_count -or $queue.Count -ne [int]$summary.notion_total) { [void]$issues.Add('SUMMARY_QUEUE_COUNT_MISMATCH') }
        if ($unique.Count -ne $queue.Count) { [void]$issues.Add('DUPLICATE_OR_MISSING_PAGE_ID') }
        if ($new.Count -ne [int]$summary.new_vs_baseline -or $baseline.Count -ne [int]$summary.baseline) { [void]$issues.Add('QUEUE_CLASSIFICATION_MISMATCH') }
        if ($pending.Count -ne $queue.Count) { [void]$issues.Add('QUEUE_ACK_OR_PROMOTION_STATUS_PRESENT') }
        if ([int]$summary.block_errors -ne 0) { [void]$issues.Add('REPORTED_BLOCK_READ_ERRORS') }
        if ($ExpectedNotionCount -gt 0 -and [int]$summary.notion_total -ne $ExpectedNotionCount) { [void]$issues.Add('CURRENT_NOTION_COUNT_DIFFERS_FROM_LOCAL_SUMMARY') }
    } catch {
        [void]$issues.Add('SUMMARY_QUEUE_PARSE_OR_FIELD_ERROR')
    }
}
if ($rawByName.ContainsKey('INCREMENTAL_ERRORS.json')) {
    $parsedErrors=ConvertFrom-Json -InputObject $rawByName['INCREMENTAL_ERRORS.json']
    if (-not ($parsedErrors -is [array])) { [void]$issues.Add('INVALID_ERRORS_ARRAY_SHAPE') }
    else {
        [object[]]$errors=$parsedErrors
        $results.counts['errorRows']=$errors.Count
        if ($errors.Count) { [void]$issues.Add('COLLECTOR_ERRORS_PRESENT') }
    }
}
# An existing Handoff file is checked for JSON parse/existence only; the owned
# source_vault_handoff_bridge.py separately verifies its exact schema and IDs.
if ($TaskName) {
    try {
        $task=Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction Stop
        $info=$task | Get-ScheduledTaskInfo -ErrorAction Stop
        $results.windowsTask=[ordered]@{
            taskChecked=$true; state=[string]$task.State
            lastRunTime=$info.LastRunTime.ToString('o'); nextRunTime=$info.NextRunTime.ToString('o')
            lastTaskResult=[int]$info.LastTaskResult
        }
        if ($info.LastTaskResult -ne 0) { [void]$issues.Add('SCHEDULED_TASK_LAST_RESULT_NONZERO') }
        # A zero task exit status alone never implies queue/Mining/Drive success.
    } catch {
        [void]$issues.Add('SCHEDULED_TASK_NOT_VERIFIABLE')
        $results.windowsTask.state='UNKNOWN'
    }
}
$results.issues=$issues.ToArray()
$results.status=if ($issues.Count) {'HOLD_LOCAL_OR_FRESHNESS_GAP'} elseif ($ExpectedNotionCount -gt 0) {
    'COUNT_MATCHES_SUPPLIED_SNAPSHOT_IDS_UNVERIFIED'
} else {'LOCAL_QUEUE_CONSISTENT_LIVE_CURRENT_UNKNOWN'}
$folder=Join-Path $outFull ('NOTION-STATUS-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$results | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $folder 'NOTION_STATUS.json') -Encoding UTF8
Write-Host ('NOTION_STATUS='+$results.status)
Write-Host ('Report folder: '+$folder)
Write-Host ('Aggregate issues: '+$issues.Count+'; no source IDs, URLs or bodies emitted.')
if ($issues.Count) { exit 2 }
exit 0
