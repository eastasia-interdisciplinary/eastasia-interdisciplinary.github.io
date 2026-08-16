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

MAX_EDGE = "480"  # displayed ~178px wide; leaves room for retina
OUT_DIR = "assets/images/people"
UA = {"User-Agent": "Mozilla/5.0"}

# Photos are shown at a fixed width with their own aspect ratio, so nothing is
# cropped and no framing decisions live here. Add an entry only if a specific
# upload genuinely needs reframing: (height, width, offsetY, offsetX) in the
# pixels of the MAX_EDGE-resized image, so a re-run reproduces it.
CROPS = {
    # shot from across a lobby, so in a square frame he ended up a small figure
    # off to one side; this pulls in to the seated figure. Note the numbers are
    # in stored pixels, and this file carries EXIF orientation 6, so its stored
    # 480x270 displays as 270x480 -- the x offset here moves the crop
    # vertically on screen.
    "이한석": (270, 270, 0, 150),
}


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


def download(file_id, dest, crop=None):
    """Fetch one photo, downscale it, normalise it to JPEG, and reframe it."""
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

    if crop:
        height, width, off_y, off_x = crop
        subprocess.run(["sips", "-c", str(height), str(width),
                        "--cropOffset", str(off_y), str(off_x), dest],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)

    listing = folder_listing(sys.argv[2])
    os.makedirs(OUT_DIR, exist_ok=True)

    # Late replies live in the pending file rather than the export; they carry
    # their Drive id directly, so they are handled on the same footing here.
    from import_people import PENDING_PATH, read_existing  # noqa: E402
    rows = [(clean(r.get("B")), clean(r.get("C")), drive_id(clean(r.get("I"))))
            for r in read_rows(sys.argv[1])]
    exported = {n for n, _, _ in rows}
    for name, entry in read_existing(PENDING_PATH).items():
        if name not in exported and entry.get("photo_drive_id"):
            rows.append((name, entry.get("name_en", ""), entry["photo_drive_id"]))

    lines, missing = [], []
    for name_ko, name_en_raw, fid in rows:
        mime = listing.get(fid, "")
        if not fid or not mime.startswith("image/"):
            missing.append(name_ko)
            continue

        filename = "%s.jpg" % slugify(name_en_raw, name_ko)
        if download(fid, os.path.join(OUT_DIR, filename), CROPS.get(name_ko)):
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
