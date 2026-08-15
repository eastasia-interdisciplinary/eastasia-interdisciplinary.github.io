#!/usr/bin/env python3
"""Download member photos from the survey's Google Drive folder.

Photos are matched to members by Drive file ID -- the survey's photo column
holds the same IDs -- rather than by the uploaded filename, which is whatever
the member's phone happened to call it.

    python3 tools/fetch_photos.py <survey export>.xlsx <drive folder url>

Writes into assets/images/people/ and prints the _data/people_photos.yml body
to paste in. Requires the Drive folder to be shared as "anyone with the link";
photos are downscaled with sips (macOS) so the repo does not carry 20 MP
phone originals for a 64px avatar.
"""

import codecs
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_people import clean, read_rows  # noqa: E402

MAX_EDGE = "480"  # displayed at 64px; leaves room for retina and future layouts
OUT_DIR = "assets/images/people"
UA = {"User-Agent": "Mozilla/5.0"}


def slugify(name_en, name_ko):
    """A stable ASCII filename stem, e.g. 'Minkyung Cho' -> 'minkyung-cho'."""
    base = unicodedata.normalize("NFKD", name_en or "")
    base = base.encode("ascii", "ignore").decode().strip().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or re.sub(r"[^a-z0-9]+", "-", name_ko.lower())


def drive_id(url):
    m = re.search(r"[-\w]{25,}", url or "")
    return m.group(0) if m else ""


def folder_listing(folder_url):
    """Return {file id: mime type} for a publicly shared Drive folder."""
    req = urllib.request.Request(folder_url, headers=UA)
    html = urllib.request.urlopen(req).read().decode("utf8", "replace")
    m = re.search(r"window\['_DRIVE_ivd'\]\s*=\s*'(.*?)';", html, re.S)
    if not m:
        sys.exit("could not read the folder listing -- is it shared publicly?")
    raw = codecs.decode(m.group(1), "unicode_escape").encode("latin-1").decode("utf-8", "replace")
    return {f[0]: f[3] for f in json.loads(raw)[0]}


def download(file_id, dest):
    """Fetch one photo, downscale it, and normalise it to JPEG."""
    url = "https://drive.google.com/uc?export=download&id=" + file_id
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req).read()
    if data[:1] == b"<" or b"<!doctype html" in data[:200].lower():
        return False  # got an interstitial rather than the image

    tmp = dest + ".orig"
    with open(tmp, "wb") as f:
        f.write(data)
    # PNG portraits cost 3-5x their JPEG equivalent for no visible gain; the
    # two with alpha channels are fully opaque anyway, so nothing is lost.
    subprocess.run(["sips", "-Z", MAX_EDGE, "-s", "format", "jpeg",
                    "-s", "formatOptions", "80", tmp, "--out", dest],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(tmp)
    return True


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)

    listing = folder_listing(sys.argv[2])
    os.makedirs(OUT_DIR, exist_ok=True)

    lines, missing = [], []
    for row in read_rows(sys.argv[1]):
        name_ko = clean(row.get("B"))
        fid = drive_id(clean(row.get("I")))
        mime = listing.get(fid, "")
        if not fid or not mime.startswith("image/"):
            missing.append(name_ko)
            continue

        filename = "%s.jpg" % slugify(clean(row.get("C")), name_ko)
        if download(fid, os.path.join(OUT_DIR, filename)):
            lines.append("%s: %s" % (name_ko, filename))
            print("  ok  %s -> %s" % (name_ko, filename))
        else:
            missing.append(name_ko)

    print("\n--- paste into _data/people_photos.yml ---")
    print("\n".join(lines))
    if missing:
        print("\nno photo for: " + ", ".join(missing))


if __name__ == "__main__":
    main()
