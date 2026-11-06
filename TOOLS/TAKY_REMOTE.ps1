$ErrorActionPreference = 'Stop'
Set-Location 'D:\Git PWA\TAKY'
$host.UI.RawUI.WindowTitle = 'TAKY | REMOTE'
Write-Host 'TAKY REMOTE — Desktop Commander Remote MCP'
$cli=Join-Path $env:APPDATA 'npm\desktop-commander.cmd'
if(-not (Test-Path -LiteralPath $cli -PathType Leaf)){ throw 'Desktop Commander CLI is not installed at the verified global path.' }
& $cli remote
