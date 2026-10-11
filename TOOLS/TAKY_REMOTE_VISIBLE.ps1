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
    $raw = Get-Content $queue -Raw -ErrorAction SilentlyContinue
    if ($raw -and $raw -ne $last) {
      $last = $raw
      if ($raw.Trim() -and -not $raw.Trim().StartsWith('#')) {
        try {
          $req = $raw | ConvertFrom-Json -ErrorAction Stop
          if (-not $req.plan_json -or -not $req.invocation_json) {
            Write-Host '[TAKY] HOLD: plan_json + invocation_json required.' -ForegroundColor Yellow
          } else {
            $runner = 'D:\Git PWA\TAKY\TOOLS\TAKY_RECEIPT_EXEC.py'
            $executorId = if ($req.executor_id) { [string]$req.executor_id } else { 'TAKY_REMOTE_VISIBLE' }
            Write-Host ''
            Write-Host ('[TAKY] receipt-bound request: ' + $req.plan_json) -ForegroundColor Yellow
            & python -X utf8 $runner --plan-json ([string]$req.plan_json) --invocation-json ([string]$req.invocation_json) --executor-id $executorId
          }
        } catch {
          Write-Host '[TAKY] INVALID/HOLD: raw command execution is disabled; queue must be receipt-bound JSON.' -ForegroundColor Red
        }
      }
    }
  } catch { Write-Host $_ -ForegroundColor Red }
  Start-Sleep -Milliseconds 700
}
