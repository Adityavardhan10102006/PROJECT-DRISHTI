# Project DRISHTI — Windows PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "PROJECT DRISHTI — Predictive Intelligence Platform"
python start.py $args
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[!] Application exited with code $LASTEXITCODE." -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit..."
}
