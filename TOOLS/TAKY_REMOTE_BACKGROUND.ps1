$ErrorActionPreference = 'SilentlyContinue'
$match = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'desktop-commander' -and $_.CommandLine -match '\bremote\b' }
if ($match) { exit 0 }
Set-Location 'D:\Git PWA\TAKY'
$env:ANTHROPIC_API_KEY = $null
$env:OPENAI_API_KEY = $null
$env:GEMINI_API_KEY = $null
$env:GOOGLE_API_KEY = $null
& npx @wonderwhy-er/desktop-commander@latest remote