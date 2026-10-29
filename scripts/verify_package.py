"""Check that a wheel contains exactly the current panel, with no old hashed assets."""

import argparse
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    expected = {
        "canovatwin/web/" + str(file.relative_to(ROOT / "src/canovatwin/web")): file.read_bytes()
        for file in (ROOT / "src/canovatwin/web").rglob("*")
        if file.is_file()
    }
    with ZipFile(args.wheel) as archive:
        actual = {
            name: archive.read(name) for name in archive.namelist() if name.startswith("canovatwin/web/")
        }
    if not expected or actual != expected:
        raise SystemExit("Wheel panel differs from the current build: missing, changed or obsolete files")
    print(f"Wheel panel verified: {len(expected)} exact files, no obsolete assets")


if __name__ == "__main__":
    main()
