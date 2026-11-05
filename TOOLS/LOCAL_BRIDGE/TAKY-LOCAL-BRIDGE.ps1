# TAKY LOCAL BRIDGE v0.3 - Windows PowerShell 5.1+; read-only inventory.
# No fetch, pull, checkout, reset, merge, Drive sync, or repository writes.
[CmdletBinding()]
param(
    [string]$Root = 'D:\Git PWA',
    [string]$DriveRoot = 'F:\',
    [string]$OutputRoot = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'TAKY-PC-Reports'),
    [switch]$SkipRemote,
    [switch]$OpenReport
)
$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$out = Join-Path $OutputRoot ('LOCAL-BRIDGE-' + $stamp)
New-Item -ItemType Directory -Path $out -Force | Out-Null
$issues = New-Object 'System.Collections.Generic.List[object]'
$inventory = New-Object 'System.Collections.Generic.List[object]'
function Add-Issue([string]$area,[string]$detail) {
    [void]$issues.Add([pscustomobject]@{ Area=$area; Detail=$detail })
}
function Git-Lines([string]$exe,[string]$repo,[string[]]$arguments) {
    $all = @('-C',$repo) + $arguments
    $result = @(& $exe @all 2>&1 | ForEach-Object { $_.ToString() })
    if ($LASTEXITCODE -ne 0) { throw "git exit $LASTEXITCODE : $($result -join ' ')" }
    foreach ($line in $result) { Write-Output ([string]$line) }
}
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) { Add-Issue 'Preflight' 'git executable missing' }
elseif (-not (Test-Path -LiteralPath $Root -PathType Container)) { Add-Issue 'Preflight' ('Missing root: '+$Root) }
else {
    $exe=$gitCmd.Source
    foreach ($dir in @(Get-ChildItem -LiteralPath $Root -Directory)) {
        $repo=$dir.FullName
        if (-not (Test-Path -LiteralPath (Join-Path $repo '.git'))) { continue }
        $branch='UNAVAILABLE'; $head='UNAVAILABLE'; $dirty='UNKNOWN'
        $remote=''; $remoteHead=''; $tracking=''; $ahead=''; $behind=''; $remoteState='SKIPPED'
        try {
            $branch=(@(Git-Lines $exe $repo @('branch','--show-current')) -join '').Trim()
            if (-not $branch) { $branch='DETACHED' }
            $head=(@(Git-Lines $exe $repo @('rev-parse','HEAD')) -join '').Trim()
            $changes=@(Git-Lines $exe $repo @('status','--porcelain','--untracked-files=normal'))
            $dirty=if (@($changes | Where-Object { ([string]$_).Trim() }).Count -gt 0) {'YES'} else {'NO'}
            try { $remote=(@(Git-Lines $exe $repo @('remote','get-url','origin')) -join '').Trim() }
            catch { $remoteState='NO_ORIGIN' }
            try { $tracking=(@(Git-Lines $exe $repo @('rev-parse','--abbrev-ref','--symbolic-full-name','@{upstream}')) -join '').Trim() }
            catch { $tracking='' }
            if ($tracking) {
                try {
                    $counts=(@(Git-Lines $exe $repo @('rev-list','--left-right','--count','HEAD...@{upstream}')) -join ' ').Trim() -split '\s+'
                    if ($counts.Length -ge 2) { $ahead=$counts[0]; $behind=$counts[1] }
                } catch { Add-Issue $dir.Name ('Tracking comparison: '+$_.Exception.Message) }
            }
            if ($remote -and -not $SkipRemote) {
                try {
                    $server=@(& $exe -c credential.interactive=never ls-remote --heads $remote main 2>&1 | ForEach-Object { $_.ToString() })
                    if ($LASTEXITCODE -ne 0) { throw ($server -join ' ') }
                    $line=@($server | Where-Object { $_ -match '^[0-9a-fA-F]{40,64}\s+refs/heads/main$' } | Select-Object -First 1)
                    if ($line.Count) { $remoteHead=($line[0] -split '\s+')[0]; $remoteState='OK' }
                    else { $remoteState='NO_MAIN_BRANCH' }
                } catch {
                    $remoteState='UNAVAILABLE'
                    Add-Issue $dir.Name ('Remote main lookup: '+$_.Exception.Message)
                }
            } elseif ($remote -and $SkipRemote) { $remoteState='SKIPPED_BY_USER' }
        } catch { Add-Issue $dir.Name $_.Exception.Message }
        [void]$inventory.Add([pscustomobject]@{
            Folder=$dir.Name; LocalPath=$repo; Branch=$branch; LocalHEAD=$head; Dirty=$dirty
            OriginURL=$remote; TrackingRef=$tracking; AheadOfTracking=$ahead; BehindTracking=$behind
            ServerMainHEAD=$remoteHead; ServerMainLookup=$remoteState
        })
    }
}
foreach ($item in $inventory) {
    if (@($item.Branch,$item.LocalHEAD,$item.OriginURL) -match 'System\.Object\[\]') {
        Add-Issue $item.Folder 'Output normalization failed'
    }
}
$inventory | Export-Csv -LiteralPath (Join-Path $out 'REPOSITORIES.csv') -NoTypeInformation -Encoding UTF8
$drive=[ordered]@{
    ConfiguredPath=$DriveRoot; Exists=$false; TopLevelItems=@()
    Notice='Metadata only; no CURRENT/HANDOFF verification, ingest, copy or synchronization.'
}
try {
    $drive.Exists=Test-Path -LiteralPath $DriveRoot -PathType Container
    if ($drive.Exists) {
        $drive.TopLevelItems=@(Get-ChildItem -LiteralPath $DriveRoot -Force | Select-Object Name,PSIsContainer,Length,LastWriteTime)
    } else { Add-Issue 'GoogleDrive' ('Missing Drive path: '+$DriveRoot) }
} catch { Add-Issue 'GoogleDrive' $_.Exception.Message }
ConvertTo-Json -InputObject $drive -Depth 5 | Out-File -LiteralPath (Join-Path $out 'DRIVE_INVENTORY.json') -Encoding UTF8
# Always emit valid JSON, including [] with zero issues (v0.2 emitted a zero-byte file).
[object[]]$issueRows=$issues.ToArray()
ConvertTo-Json -InputObject $issueRows -Depth 4 | Out-File -LiteralPath (Join-Path $out 'ERRORS.json') -Encoding UTF8
$lines=New-Object 'System.Collections.Generic.List[string]'
[void]$lines.Add('# TAKY LOCAL BRIDGE - read-only PC report')
[void]$lines.Add('Generated: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
[void]$lines.Add('Repository root: '+$Root)
[void]$lines.Add('Drive root: '+$DriveRoot)
[void]$lines.Add('Repositories detected: '+$inventory.Count)
[void]$lines.Add('Drive mounted: '+$drive.Exists)
[void]$lines.Add('')
[void]$lines.Add('## Git repositories')
[void]$lines.Add('| Folder | Branch | Local HEAD | Dirty | Server main HEAD | Server lookup |')
[void]$lines.Add('|---|---|---|---|---|---|')
foreach ($r in $inventory) {
    [void]$lines.Add('| '+$r.Folder.Replace('|','/')+' | '+$r.Branch+' | '+$r.LocalHEAD+' | '+$r.Dirty+' | '+$r.ServerMainHEAD+' | '+$r.ServerMainLookup+' |')
}
[void]$lines.Add('')
[void]$lines.Add('## Notes')
[void]$lines.Add('- ServerMainHEAD is queried from GitHub when possible, not read from local origin/main.')
[void]$lines.Add('- Ahead/behind in CSV compares against LOCAL tracking refs, potentially stale; not server main.')
[void]$lines.Add('- Drive inventory covers the mounted root only. CURRENT/HANDOFF contents not checked.')
[void]$lines.Add('- WORK-OS stays HOLD; no writes to repositories or Drive.')
[void]$lines.Add('- Review paths/URLs before sharing reports with others.')
[void]$lines.Add('')
[void]$lines.Add('## Errors')
if ($issues.Count -eq 0) { [void]$lines.Add('None recorded.') }
else { foreach ($issue in $issues) { [void]$lines.Add('- '+$issue.Area+': '+$issue.Detail) } }
$lines | Out-File -LiteralPath (Join-Path $out 'CHATGPT_REPORT.md') -Encoding UTF8
Write-Host ('Report folder: '+$out) -ForegroundColor Green
Write-Host ('Repositories: '+$inventory.Count+' | Drive mounted: '+$drive.Exists+' | Issues: '+$issues.Count)
if ($OpenReport) { Start-Process explorer.exe -ArgumentList ('"'+$out+'"') }
