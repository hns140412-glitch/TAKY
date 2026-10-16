param([switch]$Disable)
$ErrorActionPreference='Stop'
$ruleName='TAKY_USAGE_PRIVATE_LAN_8765'
$logDir=Join-Path $env:LOCALAPPDATA 'TAKY\USAGE_BOARD'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log=Join-Path $logDir 'firewall_result.txt'
function Write-Result([string]$status) {
  $stamp=(Get-Date).ToString('s')
  [IO.File]::WriteAllText($log,("$stamp "+$status),[Text.UTF8Encoding]::new($false))
}
try {
  $admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if(-not $admin) { Write-Result 'NEEDS_ELEVATION'; exit 4 }
  if($Disable) {
    Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue|Remove-NetFirewallRule -ErrorAction Stop
    Write-Result 'REMOVED'
    exit 0
  }
  $local='192.168.0.117'
  $prefix='192.168.0.0/24'
  $exe='C:\Python314\pythonw.exe'
  if(-not(Test-Path -LiteralPath $exe)) { throw 'MONITOR_EXECUTABLE_MISSING' }
  $conn=Get-NetConnectionProfile -ErrorAction Stop|Where-Object {$_.NetworkCategory -eq 'Private'}
  if(-not $conn) {throw 'NETWORK_NOT_PRIVATE'}
  $ip=Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop|Where-Object {$_.IPAddress -eq $local}
  if(-not $ip) {throw 'EXPECTED_LOCAL_IP_MISSING'}
  $old=Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
  if($old) { $old|Remove-NetFirewallRule -ErrorAction Stop }
  New-NetFirewallRule -Name $ruleName -DisplayName 'TAKY Usage Monitor (Private LAN)' -Description 'Only TAKY local usage board TCP 8765 from same router subnet. Reversible with TAKY_USAGE_FIREWALL.ps1 -Disable' -Direction Inbound -Enabled True -Action Allow -Profile Private -Protocol TCP -LocalAddress $local -LocalPort 8765 -RemoteAddress $prefix -Program $exe -EdgeTraversalPolicy Block | Out-Null
  $rule=Get-NetFirewallRule -Name $ruleName -ErrorAction Stop
  $port=$rule|Get-NetFirewallPortFilter
  $addr=$rule|Get-NetFirewallAddressFilter
  if($rule.Action -ne 'Allow' -or $rule.Profile -notmatch 'Private' -or $port.LocalPort -ne '8765' -or $addr.RemoteAddress -notcontains $prefix) {throw 'VERIFY_RULE_FAILED'}
  Write-Result 'PASS_PRIVATE_LAN_ONLY'
} catch {
  Write-Result ('FAILED_'+$_.Exception.GetType().Name)
  exit 2
}
