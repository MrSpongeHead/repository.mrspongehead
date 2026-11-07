# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 MrSpongeHead
"""Publish add-on zips into this Kodi repository.

Usage: python3 tools/publish.py [path/to/addon-x.y.z.zip ...]

- Copies each zip to zips/<id>/<id>-<version>.zip and extracts its artwork beside it
  (Kodi shows that artwork before the add-on is installed).
- Rebuilds the repository add-on zip from repository.mrspongehead/ (its own version in addon.xml).
- Keeps the newest KEEP versions of each add-on.
- Writes zips/addons.xml and zips/addons.xml.md5 from the newest version of each add-on.
- Writes index.html, the page Kodi's File manager reads, linking the repository zip.
"""

import hashlib
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIPS = os.path.join(ROOT, "zips")
REPO_ID = "repository.mrspongehead"
KEEP = 3


def version_key(version):
    return tuple(int(p) if p.isdigit() else 0 for p in re.split(r"[.\-~+]", version))


def addon_xml_from_zip(path):
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.count("/") == 1 and n.endswith("/addon.xml"))
        return archive.read(name).decode("utf-8"), archive


def add_zip(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        top = {n.split("/", 1)[0] for n in names}
        if len(top) != 1:
            raise SystemExit(f"{path}: expected one top-level folder, found {sorted(top)}")
        addon_id = top.pop()
        root = ET.fromstring(archive.read(f"{addon_id}/addon.xml"))
        if root.get("id") != addon_id:
            raise SystemExit(f"{path}: folder {addon_id} does not match add-on id {root.get('id')}")
        version = root.get("version")
        target_dir = os.path.join(ZIPS, addon_id)
        os.makedirs(target_dir, exist_ok=True)
        shutil.copyfile(path, os.path.join(target_dir, f"{addon_id}-{version}.zip"))
        assets = root.find(".//assets")
        for asset in (assets if assets is not None else []):
            if asset.text and f"{addon_id}/{asset.text}" in names:
                out = os.path.join(target_dir, asset.text)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "wb") as handle:
                    handle.write(archive.read(f"{addon_id}/{asset.text}"))
    print(f"Added {addon_id} {version}")


def build_repository_zip():
    source = os.path.join(ROOT, REPO_ID)
    version = ET.parse(os.path.join(source, "addon.xml")).getroot().get("version")
    out = os.path.join(ROOT, "dist", f"{REPO_ID}-{version}.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(os.listdir(source)):
            archive.write(os.path.join(source, name), f"{REPO_ID}/{name}")
    add_zip(out)
    for old in os.listdir(ROOT):  # only the current repository zip sits at the top level
        if old.startswith(REPO_ID + "-") and old.endswith(".zip"):
            os.remove(os.path.join(ROOT, old))
    shutil.copyfile(out, os.path.join(ROOT, os.path.basename(out)))
    return os.path.basename(out)


def prune_and_index():
    entries = []
    for addon_id in sorted(os.listdir(ZIPS)):
        folder = os.path.join(ZIPS, addon_id)
        if not os.path.isdir(folder):
            continue
        zips = sorted((f for f in os.listdir(folder) if f.startswith(addon_id + "-") and f.endswith(".zip")),
                      key=lambda f: version_key(f[len(addon_id) + 1:-4]), reverse=True)
        for old in zips[KEEP:]:
            os.remove(os.path.join(folder, old))
        if zips:
            with zipfile.ZipFile(os.path.join(folder, zips[0])) as archive:
                text = archive.read(f"{addon_id}/addon.xml").decode("utf-8")
            entries.append(re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", text).strip())
    xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + "\n".join(entries) + "\n</addons>\n"
    ET.fromstring(xml.encode("utf-8"))  # fail loudly if anything is malformed
    with open(os.path.join(ZIPS, "addons.xml"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(xml)
    with open(os.path.join(ZIPS, "addons.xml.md5"), "w", encoding="utf-8") as handle:
        handle.write(hashlib.md5(xml.encode("utf-8")).hexdigest())


def write_index(repo_zip):
    # Kodi's File manager lists links whose text matches the address, so keep them identical.
    html = ("<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>MrSpongeHead Repository</title></head>\n"
            f"<body>\n<a href=\"{repo_zip}\">{repo_zip}</a>\n</body></html>\n")
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as handle:
        handle.write(html)


def main(paths):
    os.makedirs(ZIPS, exist_ok=True)
    for path in paths:
        add_zip(path)
    repo_zip = build_repository_zip()
    prune_and_index()
    write_index(repo_zip)
    print(f"Repository zip: {repo_zip}")


if __name__ == "__main__":
    main(sys.argv[1:])
