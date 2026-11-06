chcp 65001 > $null
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
$host.UI.RawUI.WindowTitle='TAKY | REMOTE + CLAUDE LOG'
Write-Host '[REMOTE] 프로필 자동 연결 사용' -ForegroundColor Green
Write-Host '[CLAUDE LOG] 실시간 활동 표시' -ForegroundColor Cyan
python -X utf8 'D:\Git PWA\TAKY\TOOLS\TAKY_CLAUDE_LOG.py'
