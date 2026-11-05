param([switch]$DryRun)
$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $PSCommandPath
$app = Join-Path $base 'TAKY_USAGE_MOBILE_APP'
$manifest = Join-Path $app 'appsscript.json'
$serverFile = Join-Path $app 'TAKY_USAGE_MOBILE_SERVER.gs'
$stateFile = Join-Path $env:LOCALAPPDATA 'TAKY\USAGE_BOARD\mobile_cloud_state.json'
$sync = Join-Path $base 'TAKY_USAGE_MOBILE_SYNC.ps1'
if(!(Test-Path $manifest) -or !(Test-Path $serverFile)){throw 'DEPLOYMENT_FILES_MISSING'}
if($DryRun){
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $sync -DryRun
  if($LASTEXITCODE -ne 0){throw 'SYNC_DRY_RUN_FAILED'}
  $json = Get-Content -Raw -Encoding UTF8 $manifest | ConvertFrom-Json
  if($json.webapp.access -ne 'MYSELF' -or $json.webapp.executeAs -ne 'USER_DEPLOYING'){throw 'PUBLIC_ACCESS_NOT_ALLOWED'}
  Write-Output 'TAKY_MOBILE_DEPLOYMENT_PACKAGE_DRY_RUN_PASS'
  exit 0
}
Push-Location $app
try {
  $user = (& clasp.cmd show-authorized-user --json | ConvertFrom-Json)
  if(!$user.loggedIn) {
    Write-Output 'One-time authorization in the PC browser is required; do not send codes to chat.'
    & clasp.cmd login
    if($LASTEXITCODE -ne 0){throw 'GOOGLE_SIGN_IN_NOT_COMPLETED'}
  }
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $sync
  if($LASTEXITCODE -ne 0){throw 'INITIAL_CLOUD_UPLOAD_FAILED'}
  $state = Get-Content -Raw -Encoding UTF8 $stateFile | ConvertFrom-Json
  if($state.driveFileId -notmatch '^[A-Za-z0-9_-]{10,}$'){throw 'CLOUD_FILE_ID_INVALID'}
  $current = Get-Content -Raw -Encoding UTF8 $serverFile
  $patched = $current.Replace('__TAKY_USAGE_DRIVE_FILE_ID__',$state.driveFileId)
  if($patched -notmatch [regex]::Escape($state.driveFileId)){throw 'CLOUD_FILE_NOT_BOUND'}
  if($patched -ne $current){[System.IO.File]::WriteAllText($serverFile,$patched,(New-Object System.Text.UTF8Encoding($false)))}
  if(!(Test-Path '.clasp.json')){
    $manifestBackup = Get-Content -Raw -Encoding UTF8 $manifest
    & clasp.cmd create-script --title 'TAKY AI Usage Mobile' --type webapp
    if($LASTEXITCODE -ne 0){throw 'APPS_SCRIPT_CREATE_FAILED_CHECK_API_SETTINGS'}
    [System.IO.File]::WriteAllText($manifest,$manifestBackup,(New-Object System.Text.UTF8Encoding($false)))
  }
  & clasp.cmd push --force
  if($LASTEXITCODE -ne 0){throw 'APPS_SCRIPT_PUSH_FAILED'}
  $existing = (& clasp.cmd list-deployments | Out-String)
  if($LASTEXITCODE -ne 0){throw 'APPS_SCRIPT_DEPLOYMENT_QUERY_FAILED'}
  if($existing -notmatch 'TAKY AI Usage Mobile private webapp'){
    & clasp.cmd create-deployment --description 'TAKY AI Usage Mobile private webapp'
    if($LASTEXITCODE -ne 0){throw 'APPS_SCRIPT_DEPLOY_FAILED'}
  }else{ Write-Output 'APPS_SCRIPT_DEPLOYMENT_ALREADY_PRESENT' }
  & clasp.cmd list-deployments
  Write-Output 'TAKY_CLOUD_WEB_APP_DEPLOYED_NEEDS_OWNER_MOBILE_SMOKE_TEST'
  $taskName='TAKY AI Usage Mobile Sync'
  $taskAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$sync+'"')
  $trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
  $settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 2) -MultipleInstances IgnoreNew -StartWhenAvailable
  Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $trigger -Settings $settings -Force | Out-Null
  Write-Output 'TAKY_USAGE_BACKGROUND_SYNC_SCHEDULED_EVERY_5_MIN'
} finally {Pop-Location}
