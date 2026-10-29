"""Check that a wheel contains exactly the current panel, with no old hashed assets."""

import argparse
from email.parser import BytesParser
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
        metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise SystemExit("Wheel must contain exactly one package metadata file")
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
        if metadata.get("License-Expression") != "MIT" or metadata.get_all("License-File") != ["LICENSE"]:
            raise SystemExit("Wheel license metadata must declare MIT and LICENSE")
        license_path = metadata_names[0].removesuffix("METADATA") + "licenses/LICENSE"
        if (
            license_path not in archive.namelist()
            or archive.read(license_path) != (ROOT / "LICENSE").read_bytes()
        ):
            raise SystemExit("Wheel license differs from the repository LICENSE")
    if not expected or actual != expected:
        raise SystemExit("Wheel panel differs from the current build: missing, changed or obsolete files")
    print(f"Wheel panel verified: {len(expected)} exact files, no obsolete assets")
    print("Wheel MIT license metadata and license file verified")


if __name__ == "__main__":
    main()
