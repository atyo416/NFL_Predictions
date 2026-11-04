param(
    [string]$Python = ".venv\Scripts\python.exe",
    [switch]$Full,
    [switch]$LiveOdds
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
Invoke-PythonCheck -CommandArgs @('scripts/windows_preflight.py', 'runtime')
Invoke-PythonCheck -CommandArgs @('-m', 'pip', 'install', '-r', 'requirements.lock.txt')
Invoke-PythonCheck -CommandArgs @('-m', 'pip', 'install', '--no-deps', '-e', '.[test]')
Invoke-PythonCheck -CommandArgs @('-m', 'pytest', '-q')
Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', '--help')
Invoke-PythonCheck -CommandArgs @('scripts/windows_preflight.py', 'imports')
$RunStamp = Get-Date -Format 'yyyyMMddTHHmmssfff'
$BaselinePath = "reports/local_acceptance/windows-before-$RunStamp.json"
Invoke-PythonCheck -CommandArgs @('scripts/verify_local_acceptance.py', '--snapshot-only', '--baseline', $BaselinePath)
if ($Full) {
    # Validate accepted M6/M7 artifacts without refitting or reselecting their models.
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'update-history', '--start', '1999', '--end', '2017')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'audit-history')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'build-adjusted-efficiency')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'audit-personnel')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'forecast-ensemble')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'grade-ensemble')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'demo-m8')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'audit-odds')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'compare-market')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'issue-paper-bets', '--dry-run')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'settle-paper-bets')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'report-m8')
}
if ($LiveOdds) {
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'fetch-odds')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'compare-market')
    Invoke-PythonCheck -CommandArgs @('-m', 'nfl_predictor.cli', 'report-m8')
}
Invoke-PythonCheck -CommandArgs @('scripts/verify_local_acceptance.py', '--baseline', $BaselinePath)
Write-Host 'Review the saved acceptance evidence. Missing model/data or skipped upcoming games remain incomplete checks.'
Write-Host 'Start the UI manually: python -m streamlit run app.py; verify all six pages, M6/M7 sections and Betting Lab.'
Write-Host 'Record genuine Windows peak RAM/runtime separately. This script does not approve promotion or activate models.'
