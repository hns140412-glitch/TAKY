$ErrorActionPreference = 'Continue'
$repo = 'D:\Git PWA\TAKY'
Set-Location $repo

function Result($name, $state, $detail='') {
  Write-Output (('{0,-24} {1,-6} {2}' -f $name, $state, $detail).TrimEnd())
}

try {
  Get-Content '.claude\settings.json' -Raw | ConvertFrom-Json | Out-Null
  Result 'CLAUDE_SETTINGS_JSON' 'PASS'
} catch { Result 'CLAUDE_SETTINGS_JSON' 'FAIL' $_.Exception.Message }

try {
  Get-Content '.claude\settings.local.json' -Raw | ConvertFrom-Json | Out-Null
  Result 'CLAUDE_LOCAL_SETTINGS' 'PASS'
} catch { Result 'CLAUDE_LOCAL_SETTINGS' 'FAIL' $_.Exception.Message }

try {
  Get-Content '.mcp.json' -Raw | ConvertFrom-Json | Out-Null
  Result 'MCP_CONFIG_JSON' 'PASS'
} catch { Result 'MCP_CONFIG_JSON' 'FAIL' $_.Exception.Message }

python -m py_compile '.claude\hooks\taky_hook.py' '.claude\hooks\taky_outcome_hook.py' 2>$null
if ($LASTEXITCODE -eq 0) { Result 'TAKY_HOOK_COMPILE' 'PASS' } else { Result 'TAKY_HOOK_COMPILE' 'FAIL' }

$hookRegression = (& python -B 'ENFORCEMENT\claude_hook_regression.py' 2>&1 | Out-String)
if ($LASTEXITCODE -eq 0) { Result 'TAKY_HOOK_REGRESSION' 'PASS' '20/20' }
else { Result 'TAKY_HOOK_REGRESSION' 'FAIL' $hookRegression.Trim() }

$outcomeRegression = (& python -B 'ENFORCEMENT\outcome_hook_regression.py' 2>&1 | Out-String)
if ($LASTEXITCODE -eq 0) { Result 'OUTCOME_HOOK_REGRESSION' 'PASS' }
else { Result 'OUTCOME_HOOK_REGRESSION' 'FAIL' $outcomeRegression.Trim() }

$skills = @(Get-ChildItem '.claude\skills\*\SKILL.md' -File -ErrorAction SilentlyContinue)
$netlifyAuto = @($skills | Where-Object { $_.Directory.Name -like 'netlify-*' })
if ($netlifyAuto.Count -eq 1 -and $netlifyAuto[0].Directory.Name -eq 'netlify-router') {
  Result 'NETLIFY_SKILL_HYGIENE' 'PASS' ("auto=" + $skills.Count)
} else { Result 'NETLIFY_SKILL_HYGIENE' 'FAIL' ("netlify_auto=" + $netlifyAuto.Count) }

$commands = @('claude','codex','gemini','netlify')
foreach ($c in $commands) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { Result ("CLI_"+$c.ToUpper()) 'PASS' }
  else { Result ("CLI_"+$c.ToUpper()) 'FAIL' }
}
$ghExe = 'C:\Program Files\GitHub CLI\gh.exe'
if ((Get-Command gh -ErrorAction SilentlyContinue) -or (Test-Path $ghExe)) { Result 'CLI_GH' 'PASS' }
else { Result 'CLI_GH' 'FAIL' }
$codexStatus = (& codex login status 2>&1 | Out-String)
if ($codexStatus -match 'ChatGPT') { Result 'CODEX_CHATGPT_AUTH' 'PASS' }
else { Result 'CODEX_CHATGPT_AUTH' 'HOLD' 'ChatGPT login required' }

try {
  $auth = (& claude auth status 2>$null | Out-String | ConvertFrom-Json)
  if ($auth.loggedIn -and $auth.authMethod -eq 'oauth_token') {
    Result 'CLAUDE_SUBSCRIPTION_AUTH' 'PASS' 'OAuth subscription path'
  } else {
    Result 'CLAUDE_SUBSCRIPTION_AUTH' 'HOLD' ('authMethod=' + $auth.authMethod)
  }
} catch {
  Result 'CLAUDE_SUBSCRIPTION_AUTH' 'HOLD' 'Claude OAuth status unavailable'
}

$globalGemini = [Environment]::GetEnvironmentVariable('GEMINI_API_KEY','User')
if (-not $globalGemini) { $globalGemini = [Environment]::GetEnvironmentVariable('GEMINI_API_KEY','Machine') }
if ($globalGemini) { Result 'GLOBAL_GEMINI_API_KEY' 'WARN' 'TAKY launcher/wrapper clears it; do not use raw Gemini CLI outside TAKY.' }
else { Result 'GLOBAL_GEMINI_API_KEY' 'PASS' 'not set' }

$term = Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'
try {
  $t = Get-Content $term -Raw | ConvertFrom-Json
  $profile = @($t.profiles.list | Where-Object { $_.name -eq 'TAKY CLAUDE' })
  if ($profile.Count -eq 1 -and $profile[0].commandline -match 'TAKY_START.ps1') { Result 'TERMINAL_TAKY_ENTRY' 'PASS' }
  else { Result 'TERMINAL_TAKY_ENTRY' 'FAIL' }
} catch { Result 'TERMINAL_TAKY_ENTRY' 'FAIL' $_.Exception.Message }



