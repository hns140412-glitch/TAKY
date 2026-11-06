param([switch]$DryRun)
$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $PSCommandPath
$exporter = Join-Path $base 'TAKY_USAGE_MOBILE_EXPORT.py'
$uploader = Join-Path $base 'TAKY_USAGE_MOBILE_UPLOAD.mjs'
$outDir = Join-Path $env:LOCALAPPDATA 'TAKY\USAGE_BOARD'
$out = Join-Path $outDir 'mobile_usage.json'
# YKH control-center summary (local dashboard 127.0.0.1:8765, read-only, allowlisted fields).
$controlSummary = 'D:\YKH Dropbox\YKH_PERSONAL\YKH_1본부\Archi Grow\CONTROL_CENTER_PILOT\mobile_control_summary.py'
New-Item -Path $outDir -ItemType Directory -Force | Out-Null
$exportArgs = @('--output', $out)
# Scheduled sync also refreshes the account snapshot, subject to the existing
# persistent 30-minute minimum and HTTP 429 cooldown; a Drive upload alone is not a refresh.
if(-not $DryRun){$exportArgs += '--refresh-claude'}
& python -X utf8 $exporter @exportArgs
if($LASTEXITCODE -ne 0){throw 'LOCAL_EXPORT_FAILED'}
# Optional: a dashboard/summary failure must never block the usage upload.
if(Test-Path -LiteralPath $controlSummary){
  & python -B -X utf8 $controlSummary --merge $out
  if($LASTEXITCODE -ne 0){Write-Output 'YKH_CONTROL_SUMMARY_SKIPPED'}
}
if($DryRun){
  & node $uploader $out --dry-run
  if($LASTEXITCODE -ne 0){throw 'CLOUD_PROJECTION_DRY_RUN_FAILED'}
  Write-Output 'TAKY_MOBILE_SYNC_DRY_RUN_PASS'
  exit 0
}
& node $uploader $out
if($LASTEXITCODE -ne 0){throw 'CLOUD_UPLOAD_FAILED'}
Write-Output 'TAKY_MOBILE_CLOUD_SYNC_OK'
