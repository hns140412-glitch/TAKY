# TAKY Growth Observation: explicit-config, local metadata only.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ConfigPath,
    [string]$PreviousReceipt,
    [string]$ReportRoot = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'TAKY-PC-Reports'),
    [switch]$OpenReport
)
$ErrorActionPreference='Stop'
$py=Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { throw 'PYTHON_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) { throw 'CONFIG_NOT_FOUND' }
$engine=Join-Path $PSScriptRoot 'growth_observer.py'
if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) { throw 'OBSERVER_SCRIPT_NOT_INSTALLED' }
if (-not (Test-Path -LiteralPath $ReportRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $ReportRoot -Force | Out-Null
}
$out=Join-Path $ReportRoot ('GROWTH-OBSERVATION-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
$argsList=@($engine,'--config',$ConfigPath,'--output',$out)
if ($PreviousReceipt) {
    if (-not (Test-Path -LiteralPath $PreviousReceipt -PathType Leaf)) { throw 'PREVIOUS_RECEIPT_NOT_FOUND' }
    $argsList+=@('--previous',$PreviousReceipt)
}
& $py.Source @argsList
$exit=$LASTEXITCODE
Write-Host ('Observation folder: '+$out)
if ($OpenReport -and (Test-Path -LiteralPath $out)) {
    Start-Process explorer.exe -ArgumentList ('"'+$out+'"')
}
if ($exit -ne 0) { throw ('OBSERVER_REVIEW_REQUIRED_OR_FAILED: '+$exit) }
