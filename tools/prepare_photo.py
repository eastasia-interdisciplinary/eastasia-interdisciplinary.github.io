#!/usr/bin/env python3
"""Prepare a photo for the site: bake its rotation in, downscale, re-encode.

Phone photos carry their rotation as an EXIF tag rather than in the pixels.
Browsers honour it, but anything that reads the file naively does not, and
`sips -r` rotates the pixels while leaving the tag in place, which produces a
doubly-rotated image. This rotates and then clears the tag, so the file is
upright on its own terms.

    python3 tools/prepare_photo.py <source> <dest.jpg> [max-edge]

max-edge defaults to 1600, which covers a full-width image on a retina screen.
"""

import os
import struct
import subprocess
import sys

DEFAULT_MAX_EDGE = 1600
# EXIF orientation -> degrees to rotate clockwise to make the pixels upright
ROTATION = {3: 180, 6: 90, 8: 270}


def _ifd0_orientation_offset(data):
    """Byte offset of the orientation value in IFD0, or None.

    Written for the JPEG layout. HEIC keeps its EXIF somewhere else entirely,
    so the offsets read here land outside the file -- hence the guard rather
    than a crash. sips gets the rotation right when converting those anyway.
    """
    start = data.find(b"Exif\x00\x00")
    if start < 0:
        return None
    try:
        tiff = start + 6
        byte_order = ">" if data[tiff:tiff + 2] == b"MM" else "<"
        ifd = tiff + struct.unpack(byte_order + "I", data[tiff + 4:tiff + 8])[0]
        count = struct.unpack(byte_order + "H", data[ifd:ifd + 2])[0]
        for i in range(count):
            entry = ifd + 2 + i * 12
            if struct.unpack(byte_order + "H", data[entry:entry + 2])[0] == 0x0112:
                return entry + 8, byte_order
    except (struct.error, IndexError):
        return None
    return None


def read_orientation(path):
    with open(path, "rb") as f:
        data = f.read()
    found = _ifd0_orientation_offset(data)
    if not found:
        return 1
    offset, byte_order = found
    return struct.unpack(byte_order + "H", data[offset:offset + 2])[0]


def clear_orientation(path):
    """Set the tag to 1 -- the pixels are already upright by this point."""
    with open(path, "rb") as f:
        data = bytearray(f.read())
    found = _ifd0_orientation_offset(data)
    if not found:
        return
    offset, byte_order = found
    data[offset:offset + 2] = struct.pack(byte_order + "H", 1)
    with open(path, "wb") as f:
        f.write(data)


def prepare(src, dest, max_edge=DEFAULT_MAX_EDGE):
    # Only JPEG sources are rotated here. sips already applies the rotation
    # when it converts anything else, and doing it twice would undo it.
    is_jpeg = src.lower().endswith((".jpg", ".jpeg"))
    degrees = ROTATION.get(read_orientation(src), 0) if is_jpeg else 0
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)

    subprocess.run(["sips", "-Z", str(max_edge), "-s", "format", "jpeg",
                    "-s", "formatOptions", "82", src, "--out", dest],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if degrees:
        subprocess.run(["sips", "-r", str(degrees), dest],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clear_orientation(dest)
    return degrees


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    max_edge = int(sys.argv[3]) if len(sys.argv) == 4 else DEFAULT_MAX_EDGE
    degrees = prepare(sys.argv[1], sys.argv[2], max_edge)
    print("wrote %s%s" % (sys.argv[2], " (rotated %d°)" % degrees if degrees else ""))


if __name__ == "__main__":
    main()
