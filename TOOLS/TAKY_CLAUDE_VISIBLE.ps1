chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$ErrorActionPreference='Continue'
$host.UI.RawUI.WindowTitle='TAKY | Claude 작업/검토'
$queue=Join-Path $env:APPDATA 'TAKY\claude-visible-prompt.txt'
$logDir='D:\Git PWA\TAKY\HANDOFF\CLAUDE_REVIEW_LOGS'
New-Item -ItemType Directory -Force -Path (Split-Path $queue),$logDir | Out-Null
if(-not (Test-Path $queue)){ Set-Content $queue '# waiting' -Encoding UTF8 }
Write-Host 'TAKY Claude 작업/검토 준비됨' -ForegroundColor Green
Write-Host 'Claude 요청·응답·검증 로그가 여기에 표시되고 저장됩니다.' -ForegroundColor Cyan
$last=''
while($true){
  try{
    $p=Get-Content $queue -Raw -ErrorAction SilentlyContinue
    if($p -and $p -ne $last){
      $last=$p
      if($p.Trim() -and -not $p.Trim().StartsWith('#')){
        $log=Join-Path $logDir ((Get-Date -Format 'yyyyMMdd_HHmmss')+'_claude_review.log')
        Write-Host ''
        Write-Host '=== Claude 작업/검토 시작 ===' -ForegroundColor Yellow
        Write-Host $p -ForegroundColor DarkGray
        ('모든 응답과 진행 로그는 한국어로 작성하세요. 명령어, 경로, 코드, 오류 원문은 원문 그대로 둡니다.' + "`n`n" + $p) | & claude -p --model claude-sonnet-5-5 --add-dir 'D:\Git PWA\TAKY-SOURCE-VAULT' 2>&1 | ForEach-Object { $_; Add-Content -LiteralPath $log -Value $_ -Encoding UTF8 }
        Write-Host ('LOG: '+$log) -ForegroundColor DarkCyan
        Write-Host '=== Claude 작업/검토 종료 ===' -ForegroundColor Yellow
      }
    }
  } catch { Write-Host $_ -ForegroundColor Red }
  Start-Sleep -Milliseconds 700
}