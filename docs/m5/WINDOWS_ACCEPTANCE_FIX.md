# Windows PowerShell preflight correction

Windows PowerShell 5.1 can remove embedded double quotes while forwarding an inline Python `-c` argument. This produced `NameError: name 'win32' is not defined` in the first acceptance step. The later inline import check had the same quoting risk.

Both checks now execute `scripts/windows_preflight.py` with a plain argument (`runtime` or `imports`). The genuine Windows/Python 3.12 checks remain enforced. No data, model, registry or forecast logic changed.

Five targeted regression tests passed on Linux, including wrong-platform/version rejection and file invocation from a path containing spaces. PowerShell is unavailable in the cloud environment; native Windows acceptance remains pending the user's rerun. The historical M5 report's 86-test result remains its original evidence; this fix adds five tests to a fresh checkout.

For a ZIP installation, update both `scripts/windows_acceptance.ps1` and `scripts/windows_preflight.py` from the m5-historical-training branch, then rerun the acceptance command. Existing data and model folders can remain in place.
