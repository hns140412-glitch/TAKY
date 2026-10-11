chcp 65001 > $null
[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
$ErrorActionPreference='Continue'
$host.UI.RawUI.WindowTitle='Claude remote-control'
Set-Location 'D:\Git PWA\TAKY'
'ANTHROPIC_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY' | ForEach-Object {
  Remove-Item "Env:$_" -ErrorAction SilentlyContinue
}
Write-Host 'Claude remote-control' -ForegroundColor Green
Write-Host 'subscription/OAuth path / API-key fallback disabled' -ForegroundColor DarkGray
& claude remote-control
