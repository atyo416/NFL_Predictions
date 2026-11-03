"""Preflight regressions without pretending Linux provides native Windows acceptance."""
import runpy
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
validate_runtime = runpy.run_path(str(ROOT / 'scripts/windows_preflight.py'))['validate_runtime']


def test_windows_python312_is_accepted():
    validate_runtime('win32', (3, 12, 9))


@pytest.mark.parametrize('platform_name,version', [('linux', (3, 12)), ('win32', (3, 11)), ('win32', (3, 13))])
def test_wrong_platform_or_version_is_rejected(platform_name, version):
    with pytest.raises(RuntimeError):
        validate_runtime(platform_name, version)


def test_file_entry_point_with_spaces_imports_without_inline_code(tmp_path):
    directory = tmp_path / 'folder with spaces'
    directory.mkdir()
    script = directory / 'preflight check.py'
    script.write_bytes((ROOT / 'scripts/windows_preflight.py').read_bytes())
    result = subprocess.run([sys.executable, str(script), 'imports'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'imports passed' in result.stdout
