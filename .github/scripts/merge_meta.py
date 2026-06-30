#!/usr/bin/env python3
"""
Merge all meta/**/*.meta.yml files into a single meta.json.

For each device:
  - codename is used as the key
  - file paths are resolved to files/<chipset>/<filename>
  - checksums are attached to each file entry
  - commented-out file slots (auth, preloader) are skipped

Usage:
  python merge_meta.py [--verify] [--output meta.json]
"""

import hashlib
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
META_GLOB = "meta/**/*.meta.yml"
FILES_DIR = "/files"


def sha256(path: Path) -> str:
    """Return SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_files(device: dict, verify: bool = False) -> dict:
    """
    For each version, expand file entries from plain names to objects
    with name, path, and sha256. Skips None entries (commented-out slots).
    """
    chipset = device["chipset"]
    for version in device.get("versions", []):
        expanded = {}
        raw_files = version.get("files", {})
        raw_checksums = version.get("checksums", {})
        for slot, filename in raw_files.items():
            if filename is None:
                continue
            file_path = REPO_ROOT / FILES_DIR / chipset / filename
            entry = {
                "name": filename,
                "path": f"{FILES_DIR}/{chipset}/{filename}",
            }

            # Prefer checksum from meta, compute if --verify and missing
            if slot in raw_checksums and raw_checksums[slot] is not None:
                entry["sha256"] = raw_checksums[slot]
            elif verify and file_path.exists():
                entry["sha256"] = sha256(file_path)

            if verify and file_path.exists():
                if entry.get("sha256") and entry["sha256"] != sha256(file_path):
                    print(
                        f"WARNING: checksum mismatch for {file_path} (version {version['id']})",
                        file=sys.stderr,
                    )

            expanded[slot] = entry
        version["files"] = expanded
        # Drop raw checksums — they're now embedded in file entries
        version.pop("checksums", None)
    return device


def merge() -> dict:
    """Walk meta/ directory and merge all YAML files into one dict."""
    devices = {}
    for meta_file in sorted(REPO_ROOT.glob(META_GLOB)):
        with open(meta_file, "r") as f:
            device = yaml.safe_load(f)

        codename = device.get("codename")
        if not codename:
            print(f"WARNING: {meta_file} missing 'codename', skipping", file=sys.stderr)
            continue
        if codename in devices:
            print(
                f"WARNING: duplicate codename '{codename}', overwriting",
                file=sys.stderr,
            )

        devices[codename] = {
            "vendor": device.get("vendor", ""),
            "model": device.get("model", ""),
            "name": f"{device.get('vendor', '')} {device.get('model', '')}".strip(),
            "chipset": device.get("chipset", ""),
            "versions": device.get("versions", []),
        }
    return {"devices": devices}


def main():
    verify = "--verify" in sys.argv
    output = "meta.json"
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output = sys.argv[i + 1]

    data = merge()
    for codename in data["devices"]:
        data["devices"][codename] = resolve_files(
            data["devices"][codename], verify=verify
        )

    output_path = REPO_ROOT / output
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Merged {len(data['devices'])} device(s) → {output}")


if __name__ == "__main__":
    main()
