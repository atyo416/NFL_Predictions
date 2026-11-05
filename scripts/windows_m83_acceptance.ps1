$ErrorActionPreference = 'Stop'
python scripts/windows_preflight.py runtime
if ($LASTEXITCODE -ne 0) { throw 'Windows Python 3.12 preflight failed' }
python -m pytest -q tests/test_m83.py
if ($LASTEXITCODE -ne 0) { throw 'M8.3 tests failed' }
python -m nfl_predictor.cli weekly-m83 --dry-run
if ($LASTEXITCODE -ne 0) { throw 'M8.3 dry run failed; check historical cache availability' }
python -m nfl_predictor.cli weekly-m83 --report-only
if ($LASTEXITCODE -ne 0) { throw 'M8.3 report failed' }
Write-Host 'Inspect Prospective checkpoint tracking in Betting Lab after launching Streamlit.'
