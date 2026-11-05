Option Explicit
' TAKY scheduled-task windowless adapter. No network, no elevation, no model calls.
' Only known existing scheduled targets can run; preserve original args and exit code.
Dim sh, taskId, exe, opts, workdir, exitCode
If WScript.Arguments.Count <> 1 Then WScript.Quit 64
taskId = LCase(Trim(WScript.Arguments(0)))
Set sh = CreateObject("WScript.Shell")
workdir = ""
Select Case taskId
  Case "usage-mobile"
    exe = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    opts = " -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""D:\Git PWA\TAKY\TOOLS\TAKY_USAGE_MOBILE_SYNC.ps1"""
  Case "notion-discovery"
    exe = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    opts = " -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""D:\Git PWA\TAKY-SOURCE-VAULT\RUN_NOTION_INCREMENTAL_SCHEDULED.ps1"""
    workdir = "D:\Git PWA\TAKY-SOURCE-VAULT"
  Case "family-qa-daily"
    exe = "C:\Program Files\nodejs\node.exe"
    opts = " ""D:\Git PWA\TAKY\ENFORCEMENT\family_group_periodic_qa.cjs"""
  Case "family-qa-weekly"
    exe = "C:\Program Files\nodejs\node.exe"
    opts = " ""D:\Git PWA\TAKY\ENFORCEMENT\family_group_periodic_qa.cjs"" --deep"
  Case "--self-test"
    exe = sh.ExpandEnvironmentStrings("%ComSpec%")
    opts = " /D /C exit /B 0"
  Case Else
    WScript.Quit 64
End Select
If workdir <> "" Then sh.CurrentDirectory = workdir
exitCode = sh.Run(Chr(34) & exe & Chr(34) & opts, 0, True)
WScript.Quit exitCode
