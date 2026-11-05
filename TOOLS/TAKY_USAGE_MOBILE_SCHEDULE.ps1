$ErrorActionPreference='Stop'
$sync=Join-Path (Split-Path -Parent $PSCommandPath) 'TAKY_USAGE_MOBILE_SYNC.ps1'
if(!(Test-Path $sync)){throw 'SYNC_SCRIPT_NOT_FOUND'}
$taskName='TAKY AI Usage Mobile Sync'
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$sync+'"')
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 2) -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
$task=Get-ScheduledTask -TaskName $taskName
$info=Get-ScheduledTaskInfo -TaskName $taskName
Write-Output ('SCHEDULED '+$task.TaskName+' state='+$task.State+' next='+$info.NextRunTime)
Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 3
$after=Get-ScheduledTaskInfo -TaskName $taskName
Write-Output ('TRIGGERED last='+$after.LastRunTime+' result='+$after.LastTaskResult)
