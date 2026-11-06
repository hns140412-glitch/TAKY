param(
    [switch]$Once,
    [switch]$ProbeOnly
)
$ErrorActionPreference = 'Stop'
$host.UI.RawUI.WindowTitle = 'Desktop Commander Remote'
$logPath = Join-Path $env:APPDATA 'TAKY\DesktopCommanderRemote.log'
$watchdog = Join-Path $env:APPDATA 'TAKY\DesktopCommanderWatchdog.ps1'

function Get-TakyRemoteState {
    # A remote relay process alone is NOT a successful local MCP connection.
    $all = @(Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" -ErrorAction Stop)
    $relays = @($all | Where-Object { $_.CommandLine -match 'desktop-commander.*dist[\\/]+index\.js"?\s+remote\b' })
    $pairs = @(
        foreach ($r in $relays) {
            $children = @($all | Where-Object {
                $_.ParentProcessId -eq $r.ProcessId -and
                $_.CommandLine -match 'desktop-commander.*dist[\\/]+index\.js' -and
                $_.CommandLine -notmatch 'index\.js"?\s+remote\b'
            })
            if ($children.Count -gt 0) {
                [pscustomobject]@{ Relay=$r.ProcessId; Local=$children[0].ProcessId }
            }
        }
    )
    [pscustomobject]@{ Relays=$relays; Pairs=$pairs }
}

function Show-TakyRemoteLine([string]$line) {
    # Hide command parameters and JSON tool results; preserve native status/error wording.
    if ($line -match '^\[\d\d:\d\d:\d\d\]\s+\{') { return }
    if ($line -match 'Received tool call [0-9a-fA-F-]+:\s*[a-z_][a-z0-9_]*\s*\{') {
        $line = $line -replace '(Received tool call [0-9a-fA-F-]+:\s*[a-z_][a-z0-9_]*)\s*\{.*', '$1  [parameters hidden]'
    }
    if ($line -match '(?i)(access_token|refresh_token|api[_-]?key|authorization|password|session-token|secret)') {
        $line = '[sensitive content omitted]'
    }
    if ($line.Length -gt 240) { $line = $line.Substring(0,240) + ' ... [truncated]' }
    if ($line.Trim().Length) { Write-Host $line }
}

Write-Host 'Desktop Commander Remote' -ForegroundColor Cyan
Write-Host '1. Verify remote agent and local MCP BEFORE showing logs.' -ForegroundColor DarkGray

try { $state = Get-TakyRemoteState }
catch {
    Write-Host '[REMOTE] Cannot inspect process state. No connection claim or restart.' -ForegroundColor Red
    if ($Once -or $ProbeOnly) { return }
    return
}

if ($state.Pairs.Count -eq 0 -and $state.Relays.Count -eq 0) {
    if ($ProbeOnly) {
        Write-Host '[REMOTE] OFFLINE (probe-only; no launch).' -ForegroundColor Yellow
        return
    }
    Write-Host '[REMOTE] Offline. Starting once with the approved existing launcher...' -ForegroundColor Yellow
    # Another simultaneous pane cannot start a second relay.
    $mutex = [System.Threading.Mutex]::new($false, 'Local\TAKY_Remote_Profile_Startup')
    $acquired = $false
    try {
        $acquired = $mutex.WaitOne(0)
        if ($acquired) {
            $state = Get-TakyRemoteState
            if ($state.Relays.Count -eq 0) {
                if (-not (Test-Path -LiteralPath $watchdog -PathType Leaf)) {
                    Write-Host '[REMOTE] Existing approved launcher missing. No restart.' -ForegroundColor Red
                    return
                }
                & $watchdog
                # A launcher may take longer than its first three seconds.
            }
        } else {
            Write-Host '[REMOTE] Another profile instance is starting Remote; no duplicate launch.' -ForegroundColor Yellow
        }
    } catch {
        Write-Host '[REMOTE] Start failed; no repeat. Details in watchdog log.' -ForegroundColor Red
    } finally {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
    # Bounded readiness check; no endless restart or child creation.
    for ($i = 0; $i -lt 12; $i++) {
        $state = Get-TakyRemoteState
        if ($state.Pairs.Count -ge 1) { break }
        Start-Sleep -Seconds 2
    }
}

if ($state.Pairs.Count -eq 0) {
    if ($state.Relays.Count -gt 0) {
        Write-Host '[REMOTE] Relay found but LOCAL MCP is NOT READY. Logs withheld.' -ForegroundColor Red
    } else {
        Write-Host '[REMOTE] Connection not established. Logs withheld. No retry loop.' -ForegroundColor Red
    }
    return
}

if ($state.Relays.Count -gt 1 -or $state.Pairs.Count -gt 1) {
    Write-Host ('[REMOTE] WARNING: ' + $state.Relays.Count + ' relay(s) detected. No new relay started.') -ForegroundColor Yellow
}
$pair = $state.Pairs[0]
Write-Host ('[REMOTE] Relay running: PID ' + $pair.Relay) -ForegroundColor Green
Write-Host ('[MCP] Local process running: PID ' + $pair.Local) -ForegroundColor Green
Write-Host '[REMOTE] Local MCP process detected; remote tool calls provide final end-to-end proof.' -ForegroundColor DarkGray
Write-Host '[REMOTE] Automatic scheduled watchdog disabled; only profile start may launch once.' -ForegroundColor DarkGray

if ($ProbeOnly) { return }
if (-not (Test-Path -LiteralPath $logPath -PathType Leaf)) {
    Write-Host '[LOG] No file available. Agent may log in its own terminal.' -ForegroundColor Yellow
    return
}
Write-Host '[LOG] Following existing Remote log (read-only; no stale status replay).' -ForegroundColor Cyan
# The current manually started relay may write to another terminal instead of this file.
if ($Once) {
    Get-Content -LiteralPath $logPath -Encoding UTF8 -Tail 8 | ForEach-Object { Show-TakyRemoteLine $_ }
    return
}
Get-Content -LiteralPath $logPath -Encoding UTF8 -Tail 0 -Wait | ForEach-Object { Show-TakyRemoteLine $_ }
