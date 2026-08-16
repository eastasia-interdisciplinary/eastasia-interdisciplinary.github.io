#!/usr/bin/env python3
"""Lay out the people map and write _data/people_graph.yml.

Positions are computed here rather than in the browser so the page ships a
finished SVG: no layout library, no physics settling on load, and the same
picture every time, which matters when the point of the drawing is where
people sit relative to each other.

    python3 tools/build_graph.py

Layout: each field is a point on an ellipse, and its members sit on a small
ring around it. Anyone working in two fields is placed between those two
fields instead, which is what makes the overlaps visible.

Edges run from each person to their field rather than between everyone who
shares one: joining all pairs turned the largest field into a hairball of
21 lines, while spokes show the same structure and leave the two-field
members visibly reaching in two directions.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_people import read_existing  # noqa: E402

CLUSTERS_PATH = "_data/people_clusters.yml"
OUT_PATH = "_data/people_graph.yml"

# The canvas carries a margin so field names at the edges are not clipped.
WIDTH, HEIGHT = 1020, 720
CENTRE = (WIDTH / 2, HEIGHT / 2)
FIELD_RADIUS = (300, 215)   # ellipse the field centres sit on
MEMBER_RING = 96            # how far members orbit their field centre
LABEL_OFFSET = 44           # field name, pushed clear of the member ring
BRIDGE_PULL = 0.5           # 0.5 puts a two-field member exactly between them


def read_clusters(path):
    """Minimal reader for the clusters file: a field list and a name -> fields map."""
    fields, members, section = [], {}, None
    for line in open(path, encoding="utf-8"):
        line = line.split("#")[0].rstrip()
        if not line.strip():
            continue
        if line in ("fields:", "members:"):
            section = line[:-1]
            continue
        if section == "fields":
            m = re.match(r"\s*-\s*key:\s*(\S+)", line)
            if m:
                fields.append({"key": m.group(1)})
                continue
            m = re.match(r"\s*(name|name_en):\s*(.+)", line)
            if m and fields:
                fields[-1][m.group(1)] = m.group(2).strip().strip('"')
        elif section == "members":
            m = re.match(r"\s*(\S+):\s*\[(.*)\]", line)
            if m:
                members[m.group(1)] = [f.strip() for f in m.group(2).split(",") if f.strip()]
    return fields, members


def field_centres(fields):
    """One point per field, spaced evenly around an ellipse."""
    centres, n = {}, len(fields)
    for i, field in enumerate(fields):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        centres[field["key"]] = (CENTRE[0] + FIELD_RADIUS[0] * math.cos(angle),
                                 CENTRE[1] + FIELD_RADIUS[1] * math.sin(angle))
    return centres


def place(fields, members):
    centres = field_centres(fields)
    order = [f["key"] for f in fields]

    single = {k: [] for k in order}
    bridges = []
    for name, keys in members.items():
        keys = [k for k in keys if k in centres]
        if len(keys) == 1:
            single[keys[0]].append(name)
        elif len(keys) >= 2:
            bridges.append((name, keys[0], keys[1]))

    positions = {}
    for key, names in single.items():
        cx, cy = centres[key]
        count = len(names)
        # a ring, rotated so members fan away from the middle of the canvas
        facing = math.atan2(cy - CENTRE[1], cx - CENTRE[0])
        radius = MEMBER_RING if count > 1 else 0
        for i, name in enumerate(sorted(names)):
            angle = facing + (2 * math.pi * i / count if count else 0)
            positions[name] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    # two-field members sit on the line between their fields, nudged apart so
    # several bridges between the same pair do not land on one point
    seen = {}
    for name, a, b in bridges:
        pair = tuple(sorted((a, b)))
        rank = seen.get(pair, 0)
        seen[pair] = rank + 1
        (ax, ay), (bx, by) = centres[a], centres[b]
        x = ax + (bx - ax) * BRIDGE_PULL
        y = ay + (by - ay) * BRIDGE_PULL
        if rank:
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy) or 1
            offset = 46 * (1 if rank % 2 else -1) * ((rank + 1) // 2)
            x += -dy / length * offset
            y += dx / length * offset
        positions[name] = (x, y)

    return centres, positions


def spokes(members, positions, centres):
    """One line from each person to each field they work in."""
    out = []
    for name in sorted(positions):
        for key in members.get(name, []):
            if key in centres:
                out.append((positions[name], centres[key]))
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    fields, members = read_clusters(CLUSTERS_PATH)
    people = read_existing("_data/people.yml")
    unknown = [n for n in members if n not in people]
    missing = [n for n in people if n not in members]
    if unknown:
        print("not in people.yml, skipped:", ", ".join(unknown))
    if missing:
        print("no field listed, left off the map:", ", ".join(missing))

    centres, positions = place(fields, {k: v for k, v in members.items() if k in people})

    lines = ["# Generated by tools/build_graph.py -- edit _data/people_clusters.yml",
             "# instead and re-run it. Coordinates are in a %dx%d viewBox." % (WIDTH, HEIGHT),
             "", "width: %d" % WIDTH, "height: %d" % HEIGHT, "", "fields:"]
    for field in fields:
        x, y = centres[field["key"]]
        # push the label outward from the middle so it clears the member ring
        angle = math.atan2(y - CENTRE[1], x - CENTRE[0])
        lx = x + (MEMBER_RING + LABEL_OFFSET) * math.cos(angle)
        ly = y + (MEMBER_RING + LABEL_OFFSET) * math.sin(angle)
        lines += ['  - key: "%s"' % field["key"],
                  "    label_x: %.1f" % lx, "    label_y: %.1f" % ly,
                  '    name: "%s"' % field.get("name", field["key"]),
                  '    name_en: "%s"' % field.get("name_en", field.get("name", field["key"])),
                  "    x: %.1f" % x, "    y: %.1f" % y]

    lines += ["", "nodes:"]
    for name in sorted(positions):
        x, y = positions[name]
        person = people[name]
        lines += ['  - name: "%s"' % name,
                  '    name_en: "%s"' % person.get("name_en", name),
                  '    field_label: "%s"' % person.get("field", ""),
                  '    field_label_en: "%s"' % person.get("field_en", ""),
                  '    slug: "%s"' % re.sub(r"[^a-z0-9]+", "-",
                                            person.get("name_en", name).lower()).strip("-"),
                  '    fields: "%s"' % " ".join(members.get(name, [])),
                  "    x: %.1f" % x, "    y: %.1f" % y]

    lines += ["", "edges:"]
    for (ax, ay), (bx, by) in spokes({k: v for k, v in members.items() if k in people},
                                     positions, centres):
        lines += ["  - x1: %.1f" % ax, "    y1: %.1f" % ay,
                  "    x2: %.1f" % bx, "    y2: %.1f" % by]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote %s: %d nodes, %d fields" % (OUT_PATH, len(positions), len(fields)))


if __name__ == "__main__":
    main()
