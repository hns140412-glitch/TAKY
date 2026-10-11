param([string]$OutputFile = "$env:TEMP\taky_antigravity_window_check.png")
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class TakyRect {
 [StructLayout(LayoutKind.Sequential)] public struct RECT {public int Left,Top,Right,Bottom;}
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd,out RECT rect);
 [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
}
'@
$p=Get-Process 'Antigravity IDE' -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like '*TAKY-2.0-ORCH*'} | Select-Object -First 1
if(!$p){throw 'Target window missing'}
if([TakyRect]::IsIconic([IntPtr]$p.MainWindowHandle)){throw 'Target minimized'}
$r=New-Object TakyRect+RECT
if(-not [TakyRect]::GetWindowRect([IntPtr]$p.MainWindowHandle,[ref]$r)){throw 'GetWindowRect failed'}
$w=$r.Right-$r.Left;$h=$r.Bottom-$r.Top
if($w -lt 200 -or $h -lt 200 -or $w -gt 6000 -or $h -gt 4000){throw "Bad dimensions $w x $h"}
$bmp=New-Object System.Drawing.Bitmap($w,$h)
$g=[System.Drawing.Graphics]::FromImage($bmp)
try{$g.CopyFromScreen($r.Left,$r.Top,0,0,$bmp.Size)}finally{$g.Dispose()}
$bmp.Save($OutputFile,[System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "CAPTURED=$OutputFile WIDTH=$w HEIGHT=$h"
