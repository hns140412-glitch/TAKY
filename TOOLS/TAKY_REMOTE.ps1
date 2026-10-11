$ErrorActionPreference = 'Stop'
Set-Location 'D:\Git PWA\TAKY'
$host.UI.RawUI.WindowTitle = 'TAKY | REMOTE'
Write-Host 'TAKY REMOTE — Desktop Commander Remote MCP'
& npx @wonderwhy-er/desktop-commander@latest remote
