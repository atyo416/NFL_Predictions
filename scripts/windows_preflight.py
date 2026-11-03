"""File-based preflight avoids PowerShell 5.1's native inline-code quoting rules."""
import argparse
import importlib
from pathlib import Path
import sys


def validate_runtime(platform_name, version):
    if platform_name != 'win32':
        raise RuntimeError('Native Windows is required; this check cannot certify another platform.')
    if tuple(version[:2]) != (3, 12):
        raise RuntimeError(f'Python 3.12 is required; found {version[0]}.{version[1]}.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check', choices=['runtime', 'imports'])
    args = parser.parse_args()
    if args.check == 'runtime':
        validate_runtime(sys.platform, sys.version_info)
        print(sys.version)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        for name in ['nfl_predictor', 'sklearn', 'streamlit']:
            importlib.import_module(name)
        print('Project, sklearn and Streamlit imports passed.')


if __name__ == '__main__':
    main()
