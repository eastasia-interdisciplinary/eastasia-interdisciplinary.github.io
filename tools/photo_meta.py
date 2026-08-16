#!/usr/bin/env python3
"""Read the date and coordinates a phone wrote into a photo.

    python3 tools/photo_meta.py <photo.jpg> [more.jpg ...]

Prints what belongs in _data/gallery.yml. Run it on the ORIGINAL file: the
prepared copies in assets/ are re-encoded and keep only orientation.

The place name is left for a person to write. A reverse geocoder returns the
nearest point of interest, which in a dense block is routinely the wrong
building -- on the group's own photos it named a taco bar across the street
from where they actually were. Coordinates are printed so the district can be
looked up and written by hand; publishing the exact spot of a private
gathering is a choice worth making deliberately.
"""

import struct
import sys

TAGS = {0x8769: "exif_ifd", 0x8825: "gps_ifd", 0x0132: "DateTime"}
EXIF_TAGS = {0x9003: "DateTimeOriginal"}
GPS_TAGS = {0x0001: "lat_ref", 0x0002: "lat", 0x0003: "lon_ref", 0x0004: "lon"}


def _read_ifd(data, tiff, offset, order, names):
    out = {}
    if tiff + offset + 2 > len(data):
        return out
    count = struct.unpack(order + "H", data[tiff + offset:tiff + offset + 2])[0]
    for i in range(count):
        entry = tiff + offset + 2 + i * 12
        if entry + 12 > len(data):
            break
        tag, kind, n = struct.unpack(order + "HHI", data[entry:entry + 8])
        if tag not in names:
            continue
        raw = data[entry + 8:entry + 12]
        if kind == 2:  # ASCII
            at = struct.unpack(order + "I", raw)[0] if n > 4 else None
            value = (data[tiff + at:tiff + at + n] if at is not None else raw[:n])
            out[names[tag]] = value.split(b"\x00")[0].decode("utf8", "replace")
        elif kind == 5:  # rational, used for the degree/minute/second triples
            at = struct.unpack(order + "I", raw)[0]
            parts = []
            for k in range(min(n, 3)):
                num, den = struct.unpack(order + "II", data[tiff + at + k * 8:tiff + at + k * 8 + 8])
                parts.append(num / den if den else 0.0)
            out[names[tag]] = parts
        else:
            out[names[tag]] = struct.unpack(order + "I", raw)[0]
    return out


def read(path):
    with open(path, "rb") as f:
        data = f.read()
    start = data.find(b"Exif\x00\x00")
    if start < 0:
        return {}

    tiff = start + 6
    order = ">" if data[tiff:tiff + 2] == b"MM" else "<"
    ifd0 = _read_ifd(data, tiff, struct.unpack(order + "I", data[tiff + 4:tiff + 8])[0],
                     order, TAGS)

    result = {}
    taken = ifd0.get("DateTime")
    if "exif_ifd" in ifd0:
        taken = _read_ifd(data, tiff, ifd0["exif_ifd"], order, EXIF_TAGS).get(
            "DateTimeOriginal", taken)
    if taken:
        result["date"] = taken.split(" ")[0].replace(":", "-")
        result["time"] = taken.split(" ")[1] if " " in taken else ""

    if "gps_ifd" in ifd0:
        gps = _read_ifd(data, tiff, ifd0["gps_ifd"], order, GPS_TAGS)
        if gps.get("lat") and gps.get("lon"):
            def dms(parts, ref):
                value = parts[0] + parts[1] / 60 + parts[2] / 3600
                return -value if ref in ("S", "W") else value
            result["lat"] = dms(gps["lat"], gps.get("lat_ref", "N"))
            result["lon"] = dms(gps["lon"], gps.get("lon_ref", "E"))
    return result


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        meta = read(path)
        print(path.split("/")[-1])
        if not meta:
            print("  no EXIF -- messaging apps often strip it")
            continue
        if meta.get("date"):
            print("  date: %s   (%s)" % (meta["date"], meta.get("time", "")))
        if "lat" in meta:
            print("  coords: %.5f, %.5f" % (meta["lat"], meta["lon"]))
            print("  https://www.openstreetmap.org/?mlat=%.5f&mlon=%.5f#map=18/%.5f/%.5f"
                  % (meta["lat"], meta["lon"], meta["lat"], meta["lon"]))
        else:
            print("  no coordinates")


if __name__ == "__main__":
    main()
