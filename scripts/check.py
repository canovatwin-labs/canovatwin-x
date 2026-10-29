"""Run the local sprint acceptance gate with the current Python environment."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    ("ruff", "check", "src", "tests", "scripts", "setup.py"),
    ("ruff", "format", "--check", "src", "tests", "scripts", "setup.py"),
    ("pytest", "-q", "--cov=canovatwin", "--cov-report=term-missing"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", action="store_true", help="Also check, test and build the local panel")
    arguments = parser.parse_args()
    for command in CHECKS:
        result = subprocess.run([sys.executable, "-m", *command], cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    if arguments.panel:
        npm = shutil.which("npm")
        if npm is None:
            print("Panel checks need Node.js/npm; see docs/PANEL.md", file=sys.stderr)
            return 2
        return subprocess.run([npm, "run", "check"], cwd=ROOT / "web", check=False).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
