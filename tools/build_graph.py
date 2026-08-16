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
MEMBER_RING = 96            # smallest orbit for a field's members
# Names sit under the nodes, and the English ones are far wider than the
# Korean ("Seunghyeok Hwang" against 황승혁), so the orbit grows with the
# number of members to keep that much room between them whichever language
# the reader has chosen.
SPACING_PER_MEMBER = 22
LABEL_OFFSET = 118          # field name, pushed clear of the member ring
BRIDGE_PULL = 0.5           # 0.5 puts a two-field member exactly between them
BRIDGE_SPACING = 74         # gap between members bridging the same two fields
# A name is wider than its node, so nodes need more room than they look like
# they need. Sized for the longest English name in the group.
MIN_SEPARATION = 122
RELAX_STEPS = 400


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
        radius = max(MEMBER_RING, count * SPACING_PER_MEMBER) if count > 1 else 0
        for i, name in enumerate(sorted(names)):
            # half a step of rotation, so no member sits directly under the
            # field name that is placed straight outward from the centre
            step = 2 * math.pi / count if count else 0
            angle = facing + step * (i + 0.5)
            positions[name] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    # Two-field members sit on the line between their fields. Where several
    # bridge the same pair they are spread symmetrically across that line,
    # rather than one sitting on it and the others pushed off to one side.
    by_pair = {}
    for name, a, b in bridges:
        by_pair.setdefault(tuple(sorted((a, b))), []).append((name, a, b))

    for pair, group in by_pair.items():
        span = BRIDGE_SPACING * (len(group) - 1)
        for i, (name, a, b) in enumerate(sorted(group)):
            (ax, ay), (bx, by) = centres[a], centres[b]
            x = ax + (bx - ax) * BRIDGE_PULL
            y = ay + (by - ay) * BRIDGE_PULL
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy) or 1
            offset = BRIDGE_SPACING * i - span / 2
            positions[name] = (x - dy / length * offset, y + dx / length * offset)

    relax(positions)
    return centres, positions


def relax(positions):
    """Push overlapping nodes apart, pulling each back toward where it belongs.

    Placing by field and by bridge gets the structure right but says nothing
    about whether two nodes from different groups land on top of each other,
    which they do -- and the names under them collide long before the circles
    do. This settles those cases without a physics library and without any
    randomness, so the drawing is the same on every build.
    """
    ideal = dict(positions)
    names = sorted(positions)
    for _ in range(RELAX_STEPS):
        moved = False
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                ax, ay = positions[a]
                bx, by = positions[b]
                dx, dy = bx - ax, by - ay
                distance = math.hypot(dx, dy)
                if distance >= MIN_SEPARATION:
                    continue
                if distance < 1e-6:      # exactly coincident: separate sideways
                    dx, dy, distance = 1.0, 0.0, 1.0
                push = (MIN_SEPARATION - distance) / 2
                ux, uy = dx / distance, dy / distance
                positions[a] = (ax - ux * push, ay - uy * push)
                positions[b] = (bx + ux * push, by + uy * push)
                moved = True
        # a gentle pull home, so nodes do not drift away from their field
        for name in names:
            x, y = positions[name]
            ix, iy = ideal[name]
            positions[name] = (x + (ix - x) * 0.06, y + (iy - y) * 0.06)
        if not moved:
            break


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

    # The viewBox is fitted to what was actually drawn rather than assumed:
    # a field sitting at the top of the ellipse puts its name above y=0, and a
    # fixed box would clip it.
    labels = {}
    for field in fields:
        x, y = centres[field["key"]]
        angle = math.atan2(y - CENTRE[1], x - CENTRE[0])
        labels[field["key"]] = (x + (MEMBER_RING + LABEL_OFFSET) * math.cos(angle),
                                y + (MEMBER_RING + LABEL_OFFSET) * math.sin(angle))

    xs = [p[0] for p in positions.values()] + [p[0] for p in labels.values()]
    ys = [p[1] for p in positions.values()] + [p[1] for p in labels.values()]
    pad_node, pad_label = 34, 90   # node radius plus its name; label half-width
    min_x, max_x = min(xs) - pad_label, max(xs) + pad_label
    min_y, max_y = min(ys) - pad_node, max(ys) + pad_node + 18

    lines = ["# Generated by tools/build_graph.py -- edit _data/people_clusters.yml",
             "# instead and re-run it. The viewBox is fitted to the drawing.",
             "",
             "view_x: %.1f" % min_x, "view_y: %.1f" % min_y,
             "view_w: %.1f" % (max_x - min_x), "view_h: %.1f" % (max_y - min_y),
             "", "fields:"]
    for field in fields:
        x, y = centres[field["key"]]
        lx, ly = labels[field["key"]]
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
