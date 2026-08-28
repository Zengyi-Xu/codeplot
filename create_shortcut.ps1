# Create CodePlot Start Menu shortcut
$exePath = "C:\Users\Administrator\Documents\kimi\workspace\codeplot\dist\CodePlot\CodePlot.exe"
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$shortcutPath = "$startMenuPath\CodePlot.lnk"

if (-not (Test-Path $exePath)) {
    Write-Error "Executable not found: $exePath"
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $exePath
$Shortcut.WorkingDirectory = Split-Path $exePath
$Shortcut.Description = "CodePlot - Code-driven plotting tool"
$Shortcut.Save()

Write-Host "Created Start Menu shortcut: $shortcutPath"
