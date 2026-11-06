param(
    [ValidateSet('Hide','Show','Status')][string]$Mode='Status'
)
$ErrorActionPreference = 'Stop'
$statePath = Join-Path $env:LOCALAPPDATA 'TAKY\terminal_visibility.json'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class TakyWindow {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
'@
function Get-TakyVisibleTerminal {
    @(Get-Process | Where-Object {
        $_.MainWindowHandle -ne [IntPtr]::Zero -and (
            $_.ProcessName -eq 'WindowsTerminal' -or
            ($_.ProcessName -eq 'cmd' -and $_.MainWindowTitle -match '^(taky-central|taky-tunnel|.*claude\s+remote-control)')
        )
    } | Select-Object Id, ProcessName, MainWindowTitle, @{n='Handle';e={$_.MainWindowHandle.ToInt64()}})
}
if ($Mode -eq 'Status') {
    Get-TakyVisibleTerminal | Format-Table -AutoSize
    if (Test-Path -LiteralPath $statePath) {
        'Saved hidden terminal handles: ' + @((Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)).Count
    }
    return
}
if ($Mode -eq 'Hide') {
    $targets = @(Get-TakyVisibleTerminal)
    if ($targets.Count -eq 0) { 'No target terminal windows to hide'; return }
    $folder = Split-Path -Parent $statePath
    New-Item -Path $folder -ItemType Directory -Force | Out-Null
    # Save the exact PID/window handle for verified restoration; do not stop the process.
    ConvertTo-Json -InputObject $targets -Depth 3 | Set-Content -LiteralPath $statePath -Encoding UTF8
    foreach ($t in $targets) {
        [void][TakyWindow]::ShowWindow([IntPtr]::new([long]$t.Handle), 0)
        'HIDDEN PID=' + $t.Id + ' TITLE=' + $t.MainWindowTitle
    }
    return
}
if (-not (Test-Path -LiteralPath $statePath)) { 'No saved terminal windows'; return }
$targets = @(Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
foreach ($t in $targets) {
    $handle = [IntPtr]::new([long]$t.Handle)
    [uint32]$owner = 0
    if (-not [TakyWindow]::IsWindow($handle)) { continue }
    [void][TakyWindow]::GetWindowThreadProcessId($handle, [ref]$owner)
    if ($owner -ne [uint32]$t.Id) { continue }
    [void][TakyWindow]::ShowWindow($handle, 9)
    'RESTORED PID=' + $t.Id + ' TITLE=' + $t.MainWindowTitle
}
