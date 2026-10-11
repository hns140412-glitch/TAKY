$ErrorActionPreference='SilentlyContinue'
chcp 65001 > $null
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
$host.UI.RawUI.WindowTitle='TAKY | STATUS'

function ResultText($code){
  if($null -eq $code){ return '-' }
  if([int64]$code -eq 0){ return 'PASS' }
  return ('FAIL('+[string]$code+')')
}

while($true){
  Clear-Host
  $now=Get-Date
  Write-Host ('TAKY BACKGROUND STATUS  ' + $now.ToString('yyyy-MM-dd HH:mm:ss')) -ForegroundColor Cyan
  Write-Host ('-'*72) -ForegroundColor DarkGray

  $remoteProc = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'desktop-commander' -and $_.CommandLine -match '\bremote\b'
  }
  $remoteCount = @($remoteProc).Count
  if($remoteCount -gt 0){
    Write-Host ('Desktop Commander Remote : ONLINE  ('+$remoteCount+' process)') -ForegroundColor Green
  } else {
    Write-Host 'Desktop Commander Remote : OFFLINE' -ForegroundColor Red
  }

  $taskNames=@(
    'DesktopCommanderRemote',
    'TAKY Remote MCP',
    'TAKY Notion Discovery ReadOnly',
    'TAKY ReadOnly Local Audit'
  )
  Write-Host ''
  Write-Host 'SCHEDULED TASKS' -ForegroundColor Yellow
  foreach($name in $taskNames){
    $t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if(-not $t){
      Write-Host ('  '+$name+' : NOT FOUND') -ForegroundColor DarkGray
      continue
    }
    $i=Get-ScheduledTaskInfo -TaskName $name -TaskPath $t.TaskPath -ErrorAction SilentlyContinue
    $last = if($i.LastRunTime -and $i.LastRunTime.Year -gt 2000){$i.LastRunTime.ToString('MM-dd HH:mm:ss')}else{'-'}
    $next = if($i.NextRunTime -and $i.NextRunTime.Year -gt 2000){$i.NextRunTime.ToString('MM-dd HH:mm:ss')}else{'-'}
    $res=ResultText $i.LastTaskResult
    $line=('  {0,-30} {1,-8} last {2,-14} {3,-12} next {4}' -f $name,[string]$t.State,$last,$res,$next)
    if($res -eq 'PASS'){ Write-Host $line -ForegroundColor Green }
    elseif($res -like 'FAIL*'){ Write-Host $line -ForegroundColor Red }
    else { Write-Host $line }
  }

  Write-Host ''
  Write-Host 'CLAUDE' -ForegroundColor Yellow
  $claude=Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(claude|node)(\.exe)?$' -and $_.CommandLine -match 'claude' }
  Write-Host ('  active processes : '+@($claude).Count)

  $statusFile=Join-Path $env:TEMP 'TAKY_STATUSLINE_LAST.json'
  if(Test-Path $statusFile){
    try{
      $d=Get-Content $statusFile -Raw | ConvertFrom-Json
      $ctx=if($null -ne $d.context_window.used_percentage){[math]::Round([double]$d.context_window.used_percentage)}else{'?'}
      $five=if($null -ne $d.rate_limits.five_hour.used_percentage){[math]::Round(100-[double]$d.rate_limits.five_hour.used_percentage)}else{'?'}
      $week=if($null -ne $d.rate_limits.seven_day.used_percentage){[math]::Round(100-[double]$d.rate_limits.seven_day.used_percentage)}else{'?'}
      Write-Host ('  context '+$ctx+'% | 5h left '+$five+'% | 7d left '+$week+'%')
    }catch{}
  }

  Write-Host ''
  Write-Host 'Refresh: 5 sec   Ctrl+C: stop monitor' -ForegroundColor DarkGray
  Start-Sleep -Seconds 5
}
