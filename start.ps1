# Project DRISHTI — Windows PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "PROJECT DRISHTI — Command Center"

$py = "python"
if (Test-Path ".venv\Scripts\python.exe") { $py = ".venv\Scripts\python.exe" }
elseif (Test-Path "venv\Scripts\python.exe") { $py = "venv\Scripts\python.exe" }
elseif (!(Get-Command python -ErrorAction SilentlyContinue) -and (Get-Command py -ErrorAction SilentlyContinue)) { $py = "py" }

& $py start.py $args
