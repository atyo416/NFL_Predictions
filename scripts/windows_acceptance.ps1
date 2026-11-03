param(
    [string]$Python = ".venv\Scripts\python.exe",
    [switch]$Full
)
$ErrorActionPreference = "Stop"
if ($env:OS -ne "Windows_NT") { throw "This acceptance script requires genuine Windows; Linux execution cannot certify it." }
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path $Python)) { throw "Create the Python 3.12 venv first; see README.md." }
$Python = (Resolve-Path $Python).Path
function Invoke-PythonCheck {
    param([string[]]$CommandArgs)
    & $Python @CommandArgs
    if ($LASTEXITCODE -ne 0) { throw "Python acceptance step failed: $($CommandArgs -join ' ')" }
}
Invoke-PythonCheck -CommandArgs @('-c', 'import sys; assert sys.platform == "win32"; assert sys.version_info[:2] == (3,12); print(sys.version)')
Invoke-PythonCheck -CommandArgs @('-m', 'pip', 'install', '-r', 'requirements.lock.txt')
Invoke-PythonCheck -CommandArgs @('-m', 'pip', 'install', '--no-deps', '-e', '.[test]')
Invoke-PythonCheck -CommandArgs @('-m', 'pytest', '-q')
Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', '--help')
Invoke-PythonCheck -CommandArgs @('-c', 'import nfl_predictor, sklearn, streamlit; print("imports passed")')
$RunStamp = Get-Date -Format 'yyyyMMddTHHmmssfff'
$BaselinePath = "reports/local_acceptance/windows-before-$RunStamp.json"
Invoke-PythonCheck -CommandArgs @('scripts/verify_local_acceptance.py', '--snapshot-only', '--baseline', $BaselinePath)
if ($Full) {
    # Uses existing local manifest generations; no forced refresh or champion activation.
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'update-history', '--start', '1999', '--end', '2017')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'audit-history')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'compare-m4')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'compare-history')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'report-m5')
}
Invoke-PythonCheck -CommandArgs @('scripts/verify_local_acceptance.py', '--baseline', $BaselinePath)
Write-Host 'Review the saved acceptance evidence. Missing model/data or skipped upcoming games remain incomplete checks.'
Write-Host 'Start the UI manually: python -m streamlit run app.py; verify all five pages and Historical Training Analysis.'
Write-Host 'Record genuine Windows peak RAM/runtime separately. This script does not approve promotion or activate models.'
