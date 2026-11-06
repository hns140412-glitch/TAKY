chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$ErrorActionPreference='Continue'
$host.UI.RawUI.WindowTitle='TAKY | 실시간 작업 로그'
$dir=Join-Path $env:APPDATA 'TAKY'
$log=Join-Path $dir 'TAKY_LIVE.log'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
if(-not (Test-Path $log)){ New-Item -ItemType File -Path $log | Out-Null }
Write-Host 'TAKY 실시간 작업 로그 연결됨' -ForegroundColor Green
Write-Host '실행 / 검증 / PASS / FAIL이 자동 표시됩니다.' -ForegroundColor Cyan
Write-Host ''
Get-Content -LiteralPath $log -Tail 30 -Wait -Encoding UTF8
