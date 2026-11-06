chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$ErrorActionPreference = 'Continue'
$host.UI.RawUI.WindowTitle = 'TAKY | 원격 실행'
$queue = Join-Path $env:APPDATA 'TAKY\visible-command.txt'
New-Item -ItemType Directory -Force -Path (Split-Path $queue) | Out-Null
if (-not (Test-Path $queue)) { Set-Content $queue '# waiting' -Encoding UTF8 }
Write-Host 'TAKY 원격 실행 연결됨' -ForegroundColor Green
Write-Host 'ChatGPT 원격 명령과 실행 결과가 여기에 표시됩니다.' -ForegroundColor Cyan
$last = ''
while ($true) {
  try {
    $cmd = Get-Content $queue -Raw -ErrorAction SilentlyContinue
    if ($cmd -and $cmd -ne $last) {
      $last = $cmd
      if ($cmd.Trim() -and -not $cmd.Trim().StartsWith('#')) {
        Write-Host ''
        Write-Host ('> ' + $cmd) -ForegroundColor Yellow
        Invoke-Expression $cmd
      }
    }
  } catch { Write-Host $_ -ForegroundColor Red }
  Start-Sleep -Milliseconds 700
}
