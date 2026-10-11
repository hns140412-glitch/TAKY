$ErrorActionPreference='Stop'
$tools='D:\Git PWA\TAKY\TOOLS'
$remoteView=Join-Path $tools 'TAKY_DESKTOP_COMMANDER_VIEW.ps1'
$claudeLog=Join-Path $tools 'TAKY_REMOTE_LOG.ps1'
$claude=Join-Path $tools 'TAKY_CLAUDE_LAUNCH.ps1'

$args=@(
  '-w','new',
  'new-tab','--title','Desktop Commander Remote','pwsh.exe','-NoExit','-ExecutionPolicy','Bypass','-File',$remoteView,
  ';',
  'split-pane','-V','-s','0.68','--title','Claude','pwsh.exe','-NoExit','-ExecutionPolicy','Bypass','-File',$claude,
  ';',
  'move-focus','left',
  ';',
  'split-pane','-H','-s','0.50','--title','Claude background','pwsh.exe','-NoExit','-ExecutionPolicy','Bypass','-File',$claudeLog
)
& wt.exe @args
