# TAKY CONSOLE v0.1 - opt-in command wrapper for Windows PowerShell 5.1+
# No AI API access and no automatic sharing or synchronization.
[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [ValidateSet('chat','status','report','help')]
    [string]$Command = 'help',
    [ValidateSet('open','copy','path')]
    [string]$ReportAction = 'open',
    [string]$Root = 'D:\Git PWA',
    [string]$DriveRoot = 'F:\',
    [string]$ReportRoot = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'TAKY-PC-Reports'),
    [switch]$SkipRemote
)
$ErrorActionPreference='Stop'
switch ($Command) {
    'chat' {
        # Opens normal ChatGPT website, not the API. It does not inject text or gain terminal control.
        Start-Process 'https://chatgpt.com/'
        break
    }
    'status' {
        $bridge=Join-Path $PSScriptRoot 'TAKY-LOCAL-BRIDGE.ps1'
        if (-not (Test-Path -LiteralPath $bridge -PathType Leaf)) {
            throw ('Missing bridge script: '+$bridge)
        }
        $argsList=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$bridge,'-Root',$Root,'-DriveRoot',$DriveRoot,'-OutputRoot',$ReportRoot,'-OpenReport')
        if ($SkipRemote) { $argsList += '-SkipRemote' }
        & (Join-Path $PSHOME 'powershell.exe') @argsList
        if ($LASTEXITCODE -ne 0) { throw ('Bridge exited with code '+$LASTEXITCODE) }
        break
    }
    'report' {
        if (-not (Test-Path -LiteralPath $ReportRoot -PathType Container)) { throw ('No reports directory: '+$ReportRoot) }
        $dir=Get-ChildItem -LiteralPath $ReportRoot -Directory |
            Where-Object { $_.Name -like 'LOCAL-BRIDGE-*' } |
            Sort-Object Name -Descending | Select-Object -First 1
        if (-not $dir) { throw 'No LOCAL-BRIDGE report found.' }
        $file=Join-Path $dir.FullName 'CHATGPT_REPORT.md'
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw ('Missing report: '+$file) }
        switch ($ReportAction) {
            'open' { Start-Process explorer.exe -ArgumentList ('"'+$dir.FullName+'"') }
            'copy' {
                # Explicit opt-in. Review the report before pasting externally.
                Get-Content -LiteralPath $file -Raw -Encoding UTF8 | Set-Clipboard
                Write-Host 'Latest CHATGPT_REPORT.md copied to clipboard. Review before sharing.'
            }
            'path' { Write-Output $file }
        }
        break
    }
    'help' {
        @(
            'TAKY CONSOLE v0.1',
            '  taky chat                    Open normal ChatGPT in your browser',
            '  taky status                  Run read-only Local Bridge; open results folder',
            '  taky report                  Open latest report folder',
            '  taky report -ReportAction copy  Copy latest report (explicit action)',
            '  taky report -ReportAction path  Print exact latest report path',
            '  taky status -SkipRemote      Inspect PC without live remote checks',
            'Run using TAKY-CONSOLE.ps1 directly, or opt in to the profile function described in README.',
            'Does not automate ChatGPT, alter repositories, or upload reports.'
        ) | ForEach-Object { Write-Output $_ }
        break
    }
}
