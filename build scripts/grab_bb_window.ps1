param([string]$Out)
# Captures ONLY the Blockbench window, even if it is behind other windows. Never touches focus, never reads the screen.
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
}
'@
$p = Get-Process Blockbench | Where-Object MainWindowTitle | Select-Object -First 1
"title: " + $p.MainWindowTitle
"minimized: " + [Win]::IsIconic($p.MainWindowHandle)
$r = New-Object Win+RECT
[Win]::GetWindowRect($p.MainWindowHandle, [ref]$r) | Out-Null
$w = $r.R - $r.L; $h = $r.B - $r.T
"size: $w x $h"
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$dc = $g.GetHdc()
$ok = [Win]::PrintWindow($p.MainWindowHandle, $dc, 2)
$g.ReleaseHdc($dc)
"captured: $ok"
$bmp.Save($Out)
