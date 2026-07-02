#!/usr/bin/env python3
"""
Merge all meta/**/*.meta.yml files into a single meta.json.

Skips files starting with '_' (e.g. _template.meta.yml).

Output structure:
  - vendors: codenames grouped by vendor
  - devices: full details keyed by codename

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
FILES_DIR = "files"
NESTING_DEPTH = 2  # meta/<vendor>/<codename>.meta.yml


def sha256(path: Path) -> str:
    """Return SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_structure(meta_file: Path) -> str | None:
    """Check that a meta file is at the correct nesting depth. Returns error or None."""
    rel = meta_file.relative_to(REPO_ROOT)
    parts = rel.parts
    if len(parts) != NESTING_DEPTH + 1:  # meta/<vendor>/<file>.yml
        return (
            f"Wrong nesting: {rel} (expected meta/<vendor>/<codename>.meta.yml, "
            f"got {len(parts) - 2} level(s) under meta/)"
        )
    return None


def validate(data: dict) -> list[str]:
    """Run all validations. Returns list of error messages."""
    errors = []
    codenames_seen: set[str] = set()
    missing_files: set[str] = set()
    checksum_mismatches: list[str] = []

    for codename, device in data["devices"].items():
        if codename in codenames_seen:
            errors.append(f"Duplicate codename: {codename}")
        codenames_seen.add(codename)

        for version in device.get("versions", []):
            vid = version.get("id")
            if vid is None:
                errors.append(f"{codename}: version missing 'id'")
                continue

            if not version.get("files"):
                errors.append(f"{codename} v{vid}: no files specified")

            for slot, entry in version.get("files", {}).items():
                file_path = REPO_ROOT / entry["path"]
                if not file_path.exists():
                    missing_files.add(entry["path"])
                    continue

                actual_sha = sha256(file_path)
                if entry.get("sha256") and entry["sha256"] != actual_sha:
                    checksum_mismatches.append(
                        f"{entry['path']} (version {vid}, {slot}): "
                        f"expected {entry['sha256'][:12]}..., got {actual_sha[:12]}..."
                    )

    for path in sorted(missing_files):
        errors.append(f"File not found: {path}")
    errors.extend(checksum_mismatches)

    return errors


def resolve_files(device: dict) -> dict:
    """
    For each version, expand file entries from plain names to objects
    with name, path (flat files/<name>), and sha256. Skips None entries.
    """
    for version in device.get("versions", []):
        expanded = {}
        raw_files = version.get("files", {})
        raw_checksums = version.get("checksums", {})
        for slot, filename in raw_files.items():
            if filename is None:
                continue
            entry = {
                "name": filename,
                "path": f"{FILES_DIR}/{filename}",
            }
            if slot in raw_checksums and raw_checksums[slot] is not None:
                entry["sha256"] = raw_checksums[slot]
            expanded[slot] = entry
        version["files"] = expanded
        version.pop("checksums", None)
    return device


def merge() -> dict:
    """Walk meta/ directory, skip templates (_*), merge YAML into one dict."""
    devices = {}
    vendors = {}
    structure_errors: list[str] = []

    for meta_file in sorted(REPO_ROOT.glob(META_GLOB)):
        # Skip template files
        if meta_file.name.startswith("_"):
            continue

        # Validate nesting depth
        err = validate_structure(meta_file)
        if err:
            structure_errors.append(err)
            continue

        with open(meta_file, "r") as f:
            device = yaml.safe_load(f)

        codename = device.get("codename")
        if not codename:
            print(f"WARNING: {meta_file} missing 'codename', skipping", file=sys.stderr)
            continue
        if codename in devices:
            print(
                f"WARNING: duplicate codename '{codename}' in {meta_file}, skipping",
                file=sys.stderr,
            )
            continue

        vendor = device.get("vendor", "")
        model = device.get("model", "")
        name = device.get("name") or f"{vendor} {model}".strip()

        devices[codename] = {
            "vendor": vendor,
            "model": model,
            "name": name,
            "versions": device.get("versions", []),
        }

        vendors.setdefault(vendor, []).append(codename)

    if structure_errors:
        print("STRUCTURE ERRORS:", file=sys.stderr)
        for e in structure_errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    for v in vendors:
        vendors[v].sort()

    return {"vendors": vendors, "devices": devices}


def main():
    verify = "--verify" in sys.argv
    output = "meta.json"
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output = sys.argv[i + 1]

    data = merge()
    for codename in data["devices"]:
        data["devices"][codename] = resolve_files(data["devices"][codename])

    # Validate
    errors = validate(data)
    if errors:
        print(f"VALIDATION FAILED ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    if verify:
        print("VALIDATION PASSED")

    output_path = REPO_ROOT / output
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Merged {len(data['devices'])} device(s) → {output}")


if __name__ == "__main__":
    main()
