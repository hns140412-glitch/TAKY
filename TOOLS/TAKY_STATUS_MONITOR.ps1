param([switch]$PcGuard,[switch]$GuardOnce)
if($PcGuard){
  # TAKY lightweight PC resource guard. No process termination or working-set trimming.
  $ErrorActionPreference='SilentlyContinue'
  $mutex=[System.Threading.Mutex]::new($false,'Local\TAKY_PC_GUARD_SINGLETON')
  if(-not $mutex.WaitOne(0)){ exit 0 }
  $root=Join-Path $env:LOCALAPPDATA 'TAKY\PC_GUARD'
  New-Item -ItemType Directory -Path $root -Force | Out-Null
  $snapshotFile=Join-Path $root 'status.json'
  $eventFile=Join-Path $root 'events.log'
  $guardStartedAt=Get-Date
  $previousCpu=@{}
  $previousAt=Get-Date
  $ramHighSamples=0
  $cpuHighSamples=0
  function Record-GuardEvent([string]$message){
    ('{0} {1}' -f (Get-Date).ToString('s'),$message) | Add-Content -LiteralPath $eventFile -Encoding UTF8
  }
  # Browser startup boosters frequently register again after updates.
  # Suppress only named background auto-launch entries; do not touch browser sessions.
  function Suppress-BrowserAutoStart{
    $run='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    $properties=@((Get-ItemProperty -Path $run).PSObject.Properties |
      Where-Object { $_.Name -match '^(MicrosoftEdgeAutoLaunch_|GoogleChromeAutoLaunch_)' })
    foreach($property in $properties){
      Remove-ItemProperty -Path $run -Name $property.Name -ErrorAction Stop
      Record-GuardEvent ('SUPPRESSED_BROWSER_AUTORUN '+$property.Name)
    }
  }
  Suppress-BrowserAutoStart
  $lastDriveState=-1
  function Sample-Guard{
    # Enforce at each 30-second sample because browsers may re-register auto-launch.
    Suppress-BrowserAutoStart
    $os=Get-CimInstance Win32_OperatingSystem
    if(-not $os){ Record-GuardEvent 'OS_SNAPSHOT_FAILED';return }
    $ramTotal=[double]$os.TotalVisibleMemorySize
    $ramPercent=[math]::Round(100*(1-[double]$os.FreePhysicalMemory/$ramTotal),1)
    $procs=@(Get-Process -ErrorAction SilentlyContinue)
    $counts=@{}
    $currentCpu=@{}
    foreach($p in $procs){
      $n=[string]$p.ProcessName
      if(-not $counts.ContainsKey($n)){$counts[$n]=[pscustomobject]@{Count=0;MB=0.0}}
      $counts[$n].Count++
      $counts[$n].MB += [double]$p.WorkingSet64/1MB
      try { $currentCpu[[int]$p.Id]=[double]$p.CPU }catch{}
    }
    $now=Get-Date
    $elapsed=[math]::Max(1,($now-$script:previousAt).TotalSeconds)
    $cpuCores=[Environment]::ProcessorCount
    $cpuMax=0.0
    $hotNames=New-Object System.Collections.Generic.List[string]
    foreach($p in $procs){
      $pidKey=[int]$p.Id
      if($script:previousCpu.ContainsKey($pidKey) -and $currentCpu.ContainsKey($pidKey)){
        $delta=$currentCpu[$pidKey]-$script:previousCpu[$pidKey]
        $pct=[math]::Round(100*[math]::Max(0,$delta)/$elapsed/$cpuCores,1)
        if($pct -gt $cpuMax){$cpuMax=$pct}
        if($pct -ge 40){$hotNames.Add(('{0}:{1}%' -f $p.ProcessName,$pct))}
      }
    }
    $script:previousCpu=$currentCpu
    $script:previousAt=$now
    $script:ramHighSamples=if($ramPercent -ge 85){$script:ramHighSamples+1}else{0}
    $script:cpuHighSamples=if($hotNames.Count -gt 0){$script:cpuHighSamples+1}else{0}
    $largest=@($counts.GetEnumerator() | Sort-Object {$_.Value.MB} -Descending | Select-Object -First 8 | ForEach-Object {[pscustomobject]@{name=$_.Key;count=$_.Value.Count;ramMB=[math]::Round($_.Value.MB)}})
    $drive=@(Get-Process -Name GoogleDriveFS -ErrorAction SilentlyContinue).Count
    $state=[ordered]@{
      updatedAt=$now.ToString('o');status=if($GuardOnce){'SNAPSHOT_ONLY'}else{'RUNNING'}; mode=if($GuardOnce){'STARTUP_OBSERVATION_NO_RESIDENT_MONITOR'}else{'SAFE_NO_KILL'}
      osLastBootAt=$os.LastBootUpTime.ToString('o')
      guardStartedAt=$script:guardStartedAt.ToString('o')
      autorunConfigured=([string](Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run').'TAKY Status Monitor' -match 'TAKY_STATUS_MONITOR\.ps1.+-PcGuard')
      ramTotalGB=[math]::Round($ramTotal/1MB,2);ramUsedPercent=$ramPercent
      cpuLargestProcessPercent=$cpuMax;hotCpuProcesses=@($hotNames)
      googleDriveProcesses=$drive;topMemory=$largest
      ramAlert=($script:ramHighSamples -ge 3);cpuAlert=($script:cpuHighSamples -ge 3)
    }
    $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $snapshotFile -Encoding UTF8
    if($script:ramHighSamples -eq 3){Record-GuardEvent ('SUSTAINED_RAM_PRESSURE '+$ramPercent+'%; no forced termination')}
    if($script:cpuHighSamples -eq 3){Record-GuardEvent ('SUSTAINED_CPU_PRESSURE '+($hotNames -join ',')+'; no forced termination')}
    if($drive -ne $script:lastDriveState){
      if($drive -eq 0){Record-GuardEvent 'GOOGLE_DRIVE_NOT_RUNNING (check sync, no automatic force-relaunch)'}
      elseif($script:lastDriveState -eq 0){Record-GuardEvent ('GOOGLE_DRIVE_REAPPEARED processes='+$drive)}
      $script:lastDriveState=$drive
    }
  }
  try {
    Record-GuardEvent 'START resource guard; protects active work; 30s sampling'
    Sample-Guard
    if($GuardOnce){exit 0}
    while($true){Start-Sleep -Seconds 30;Sample-Guard}
  }finally{ $mutex.ReleaseMutex() | Out-Null; $mutex.Dispose() }
  exit 0
}
$ErrorActionPreference='SilentlyContinue'
chcp 65001 > $null
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
$host.UI.RawUI.WindowTitle='TAKY | STATUS'
# Prevent duplicate monitor loops across manually launched and scheduled sessions.
$monitorMutex = [System.Threading.Mutex]::new($false,'Local\TAKY_STATUS_MONITOR_SINGLETON')
if(-not $monitorMutex.WaitOne(0)){ Write-Host 'TAKY monitor already running'; exit 0 }

function ResultText($code){
  if($null -eq $code){ return '-' }
  if([int64]$code -eq 0){ return 'PASS' }
  return ('FAIL('+[string]$code+')')
}

# CPU guard: 5-second samples; no automatic termination of live work.
$cpuThreshold = 40.0
$cpuSustainSeconds = 30
$cpuLast = @{}
$cpuHighSince = @{}
$cpuReported = @{}
$cpuAlertFile = Join-Path $env:TEMP 'TAKY_CPU_GUARD_EVENTS.csv'
function Get-TakyCpuGroups {
  $snapshot = @(Get-CimInstance Win32_Process)
  $byPid = @{}
  foreach($entry in $snapshot){ $byPid[[int]$entry.ProcessId] = $entry }
  $processes = @(Get-Process -ErrorAction SilentlyContinue)
  $cpuByPid = @{}
  foreach($p in $processes){ try { $cpuByPid[[int]$p.Id] = [double]$p.CPU } catch {} }
  $groups = @{}
  foreach($entry in $snapshot){
    $root = $entry
    $seen = @{}
    while($root -and $root.Name -notin @('pwsh.exe','powershell.exe')){
      if($seen.ContainsKey([int]$root.ProcessId)){ $root=$null; break }
      $seen[[int]$root.ProcessId] = $true
      $parent = $byPid[[int]$root.ParentProcessId]
      if(-not $parent -or $parent.CreationDate -gt $root.CreationDate){ $root=$null; break }
      $root = $parent
    }
    if($root -and $root.Name -in @('pwsh.exe','powershell.exe')){
      $key = [string]$root.ProcessId
      if(-not $groups.ContainsKey($key)){ $groups[$key] = @{Cpu=0.0; Count=0; Command=[string]$root.CommandLine} }
      if($cpuByPid.ContainsKey([int]$entry.ProcessId)){
        $groups[$key].Cpu += $cpuByPid[[int]$entry.ProcessId]
      }
      $groups[$key].Count++
    }
  }
  return $groups
}
$cpuPreviousTime = Get-Date
$cpuPreviousGroups = Get-TakyCpuGroups

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
  Write-Host 'CPU GROUP GUARD (40% for 30 sec)' -ForegroundColor Yellow
  $cpuCurrentGroups = Get-TakyCpuGroups
  $cpuElapsed = [math]::Max(0.1,((Get-Date)-$cpuPreviousTime).TotalSeconds)
  $cpuNow = Get-Date
  $cpuCores = [Environment]::ProcessorCount
  foreach($key in @($cpuCurrentGroups.Keys)){
    $item = $cpuCurrentGroups[$key]
    if($cpuPreviousGroups.ContainsKey($key)){
      $delta = $item.Cpu - $cpuPreviousGroups[$key].Cpu
      $percent = [math]::Round(100 * [math]::Max(0,$delta) / $cpuElapsed / $cpuCores,1)
      if($percent -ge $cpuThreshold){
        if(-not $cpuHighSince.ContainsKey($key)){ $cpuHighSince[$key] = $cpuNow }
        $duration = [math]::Round(($cpuNow-$cpuHighSince[$key]).TotalSeconds)
        Write-Host ('  PowerShell tree PID '+$key+' : '+$percent+'%  '+$duration+'s  children '+$item.Count) -ForegroundColor Red
        if($duration -ge $cpuSustainSeconds -and -not $cpuReported.ContainsKey($key)){
          $cpuReported[$key] = $true
          [pscustomobject]@{Timestamp=$cpuNow.ToString('o'); RootPID=$key; CpuPercent=$percent; Seconds=$duration; ProcessCount=$item.Count; Command=$item.Command} | Export-Csv -Path $cpuAlertFile -NoTypeInformation -Append -Encoding utf8
          Write-Host ('  ALERT RECORDED: '+$cpuAlertFile) -ForegroundColor Red
        }
      }else{
        $cpuHighSince.Remove($key) | Out-Null
        $cpuReported.Remove($key) | Out-Null
      }
    }
  }
  foreach($key in @($cpuHighSince.Keys)){
    if(-not $cpuCurrentGroups.ContainsKey($key)){
      $cpuHighSince.Remove($key) | Out-Null
      $cpuReported.Remove($key) | Out-Null
    }
  }
  $cpuPreviousGroups = $cpuCurrentGroups
  $cpuPreviousTime = $cpuNow
  if($cpuHighSince.Count -eq 0){ Write-Host '  No sustained PowerShell-tree overload detected' -ForegroundColor Green }
  Write-Host ''
  Write-Host 'Refresh: 5 sec   Ctrl+C: stop monitor' -ForegroundColor DarkGray
  Start-Sleep -Seconds 5
}
