chcp 65001 > $null
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
$host.UI.RawUI.WindowTitle='Claude CLI Activity Log'
Write-Host '[REMOTE] 수동 연결 유지 | 자동 재시작 없음' -ForegroundColor Green
Write-Host '[CLAUDE LOG] 실시간 활동 표시' -ForegroundColor Cyan
python -X utf8 'D:\Git PWA\TAKY\TOOLS\TAKY_CLAUDE_LOG.py'
