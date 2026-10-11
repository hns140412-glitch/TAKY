chcp 65001 > $null
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
$host.UI.RawUI.WindowTitle='Desktop Commander Remote'
$dir=Join-Path $env:APPDATA 'TAKY'
$log=Join-Path $dir 'DesktopCommanderRemote.log'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
if(-not (Test-Path $log)){ New-Item -ItemType File -Path $log | Out-Null }
Write-Host 'Desktop Commander Remote — ChatGPT PC bridge' -ForegroundColor Green
Write-Host '스케줄러 watchdog 연결 / 아래는 실제 remote 출력' -ForegroundColor DarkGray
Write-Host ''
Get-Content -LiteralPath $log -Tail 40 -Wait -Encoding UTF8
