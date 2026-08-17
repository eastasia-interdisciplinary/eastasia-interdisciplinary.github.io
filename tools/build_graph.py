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
FIELD_RADIUS = (470, 335)   # ellipse the field centres sit on
MEMBER_RING = 132           # smallest orbit for a field's members
SPACING_PER_MEMBER = 30     # orbit grows with the size of the field
LABEL_OFFSET = 46           # field name, kept against its hub
LABEL_ARC = math.radians(96)  # slice of each ring kept clear for that name
# Not 0.5. Sitting exactly between two fields says both are equally theirs,
# which is wrong for someone like 이유경, whose 한국음악 is art first and history
# second. The first field listed for a member is read as the primary one and
# they are placed nearer to it, still visibly reaching toward the other.
BRIDGE_PULL = 0.36
BRIDGE_SPACING = 92         # gap between members bridging the same two fields
# Nodes carry no name -- hovering one puts the person in the panel -- so the
# spacing only has to keep the portraits apart, not the words that used to sit
# under them. That is what pays for the larger nodes and the tighter map.
NODE_RADIUS = 30            # keep in step with the r= in people.html
MIN_SEPARATION = NODE_RADIUS * 2 + 44
# Two spokes leaving the same field at nearly the same bearing are hard to
# tell apart, however far apart their nodes are, so members are also kept
# apart by angle as seen from their field.
MIN_SPOKE_ANGLE = math.radians(19)
# A spoke passing across someone else's portrait reads as a connection they
# do not have, so unrelated nodes are pushed off the line.
EDGE_CLEARANCE = NODE_RADIUS + 14
RELAX_STEPS = 700
NAME_DROP = 0


def read_clusters(path):
    """Minimal reader for the clusters file: a field list and a name -> fields map."""
    fields, members, section = [], {}, None
    for line in open(path, encoding="utf-8"):
        # a comment needs whitespace before it, so a colour like "#55703c" survives
        line = re.sub(r"\s+#.*$", "", line).rstrip()
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
            m = re.match(r"\s*(name|name_en|color):\s*(.+)", line)
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
    half_widths = {f["key"]: label_half_width(f) for f in fields}

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
        # The field name occupies the middle, so the ring has to clear it --
        # "Natural Sciences & Engineering" is wider than the default orbit.
        radius = max(MEMBER_RING, count * SPACING_PER_MEMBER,
                     half_widths[key] + NODE_RADIUS + 20)
        for i, name in enumerate(sorted(names)):
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
            x, y = x - dy / length * offset, y + dx / length * offset
            # a bridge lands between two hubs, which is where the field names
            # now are; slide it along the line until it is clear of both
            for hub in (a, b):
                hx, hy = centres[hub]
                need = half_widths[hub] + NODE_RADIUS + 16
                while abs(x - hx) < need and abs(y - hy) < LABEL_HALF_H + NODE_RADIUS + 16:
                    x += (bx - ax) / length * 8 * (1 if hub == a else -1)
                    y += (by - ay) / length * 8 * (1 if hub == a else -1)
            positions[name] = (x, y)

    return centres, positions



def relax(positions, labels=None, half_widths=None, fields_of=None, centres=None):
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

        # members spread out from each other
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

        # spread the spokes leaving each field, so no two run along the same
        # bearing; rotating around the hub keeps each spoke its own length
        if fields_of and centres:
            for key, (hx, hy) in centres.items():
                mine = [n for n in names if key in fields_of.get(n, [])]
                for i, a in enumerate(mine):
                    for b in mine[i + 1:]:
                        ax, ay = positions[a]
                        bx, by = positions[b]
                        angle_a = math.atan2(ay - hy, ax - hx)
                        angle_b = math.atan2(by - hy, bx - hx)
                        gap = (angle_b - angle_a + math.pi) % (2 * math.pi) - math.pi
                        if abs(gap) >= MIN_SPOKE_ANGLE:
                            continue
                        turn = (MIN_SPOKE_ANGLE - abs(gap)) / 2
                        turn = turn if gap >= 0 else -turn
                        for name, sign in ((a, -1), (b, 1)):
                            x, y = positions[name]
                            dx, dy = x - hx, y - hy
                            t = sign * turn
                            positions[name] = (hx + dx * math.cos(t) - dy * math.sin(t),
                                               hy + dx * math.sin(t) + dy * math.cos(t))
                        moved = True

        # keep spokes off portraits they have nothing to do with
        if fields_of and centres:
            for name in names:
                px, py = positions[name]
                for other in names:
                    if other == name:
                        continue
                    for key in fields_of.get(other, []):
                        if key in fields_of.get(name, []) and other == name:
                            continue
                        hx, hy = centres[key]
                        ox, oy = positions[other]
                        vx, vy = hx - ox, hy - oy
                        length_sq = vx * vx + vy * vy
                        if length_sq < 1:
                            continue
                        t = max(0.0, min(1.0, ((px - ox) * vx + (py - oy) * vy) / length_sq))
                        cx, cy = ox + t * vx, oy + t * vy
                        dx, dy = px - cx, py - cy
                        distance = math.hypot(dx, dy)
                        if distance >= EDGE_CLEARANCE or 0.02 > t or t > 0.98:
                            continue
                        if distance < 1e-6:
                            dx, dy, distance = -vy, vx, math.hypot(vx, vy)
                        push = EDGE_CLEARANCE - distance
                        px += dx / distance * push
                        py += dy / distance * push
                        positions[name] = (px, py)
                        moved = True

        # and last, out of the field names. Radially, away from the centre the
        # ring already runs around, so it cannot bounce a node into the next
        # name; and last in the iteration so separation cannot undo it.
        if labels:
            for name in names:
                x, y = positions[name]
                for key, (lx, ly) in labels.items():
                    need_x = half_widths[key] + NODE_RADIUS + CHIP_CLEARANCE
                    need_y = CHIP_HALF_H + NODE_RADIUS + CHIP_CLEARANCE
                    if abs(x - lx) >= need_x or abs(y - ly) >= need_y:
                        continue
                    dx, dy = x - lx, y - ly
                    distance = math.hypot(dx, dy)
                    ux, uy = (dx / distance, dy / distance) if distance > 1 else (1.0, 0.0)
                    while abs(x - lx) < need_x and abs(y - ly) < need_y:
                        x += ux * 6
                        y += uy * 6
                    positions[name] = (x, y)
                    moved = True


        if not moved:
            break



LABEL_HALF_H = 20
CHIP_PAD = 38            # breathing room either side of a field name
CHIP_HALF_H = 27         # half the chip's height, per chip_h below
CHIP_CLEARANCE = 24      # gap left between a chip and the nearest portrait
LABEL_FONT = 32          # keep in step with .map-fields text in the CSS


def label_clear(x, y, half_w, positions):
    """True if the label's box misses every node's box.

    A node's box is its circle plus the name printed under it, so a label
    slipping into the gap between two circles still counts as a collision --
    it would land on their names.
    """
    l_left, l_right = x - half_w, x + half_w
    l_top, l_bottom = y - CHIP_HALF_H, y + CHIP_HALF_H
    for nx, ny in positions.values():
        n_left, n_right = nx - NODE_RADIUS - 8, nx + NODE_RADIUS + 8
        n_top, n_bottom = ny - NODE_RADIUS - 4, ny + NAME_DROP + 6
        if l_right > n_left and l_left < n_right and l_bottom > n_top and l_top < n_bottom:
            return False
    return True


NARROW = "·・-–— .,&"


def text_width(text):
    """Rendered width of a name, measured against the display serif.

    Korean glyphs run about the full point size, Latin about half, and
    punctuation like the interpunct a good deal less than either.
    """
    total = 0.0
    for char in text:
        if char in NARROW:
            total += LABEL_FONT * 0.34
        elif ord(char) > 0x2000:      # CJK and Hangul
            total += LABEL_FONT
        else:
            total += LABEL_FONT * 0.47
    return total


def label_half_width(field):
    """Half the chip's width, for keeping members clear of it."""
    return max(text_width(field.get("name", "")),
               text_width(field.get("name_en", ""))) / 2 + CHIP_PAD / 2 + 6


def box_free(x, y, half_w, positions, taken):
    """Is a label box at (x, y) clear of every node, its name, and every label
    already placed?"""
    for nx, ny in positions.values():
        if (abs(nx - x) < half_w + NODE_RADIUS + 10
                and y + LABEL_HALF_H > ny - NODE_RADIUS - 10
                and y - LABEL_HALF_H < ny + NAME_DROP + 10):
            return False
    for tx, ty, t_half in taken:
        if abs(tx - x) < half_w + t_half + 14 and abs(ty - y) < LABEL_HALF_H * 2 + 10:
            return False
    return True


def nudge_labels(labels, centres, positions, half_widths):
    """Last resort: if a member still sits on a field name, move the name.

    Members are pushed out of the names during relaxation, but one caught
    between two names can be shoved out of the first and into the second and
    back. The names have somewhere to go and are few, so whoever is left over
    is settled by moving the name outward instead, which always terminates.
    """
    for key, (lx, ly) in list(labels.items()):
        cx, cy = centres[key]
        angle = math.atan2(cy - CENTRE[1], cx - CENTRE[0])
        for _ in range(60):
            clash = any(abs(x - lx) < half_widths[key] + NODE_RADIUS + CHIP_CLEARANCE
                        and abs(y - ly) < CHIP_HALF_H + NODE_RADIUS + CHIP_CLEARANCE
                        for x, y in positions.values())
            if not clash:
                break
            lx += 12 * math.cos(angle)
            ly += 12 * math.sin(angle)
        labels[key] = (lx, ly)


def place_labels(fields, centres, positions):
    """The field name is the hub.

    A dot and a name beside it were two marks for one thing, and whenever the
    name got pushed off it needed a leader line to say which dot it belonged
    to. The name sits at the centre instead, the members ring it, and the
    spokes run to the name itself.
    """
    return {f["key"]: centres[f["key"]] for f in fields}


PAGE_BG = (0xf6, 0xf4, 0xec)   # --bg; keep in step with the stylesheet
CHIP_TINT = 0.13               # how much of the field's colour the chip carries


def glow_colour(hex_colour, alpha=0.3):
    """The field's colour as a translucent rgba, for the chip's soft halo."""
    value = hex_colour.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return "rgba(%d, %d, %d, %.2f)" % (r, g, b, alpha)


def chip_colour(hex_colour):
    """The field's colour mixed into the page colour, as a solid.

    A translucent chip let the spokes show straight through it, which read as
    lines running over the name. Blending here instead means the chip is
    opaque -- it hides what passes behind it -- while still looking like a
    wash rather than a filled box.
    """
    value = hex_colour.lstrip("#")
    rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    mixed = tuple(round(bg * (1 - CHIP_TINT) + fg * CHIP_TINT)
                  for bg, fg in zip(PAGE_BG, rgb))
    return "#%02x%02x%02x" % mixed


def colour_of(fields, key):
    for field in fields:
        if field["key"] == key:
            return field.get("color", "#55703c")
    return "#55703c"


def territory(points, padding=52, rays=64):
    """A closed blob enclosing a field's members.

    Distance from a hub does not tell a reader who belongs to it: 정재우 works
    only in 어문 but ends up as near the 자연과학 hub as 조민경, who actually
    works in both. Drawing the fields as areas answers that directly -- inside
    one is membership, inside the overlap of two is the interdisciplinary
    case -- and the overlaps deepen in tint on their own.
    """
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)

    ring = []
    for i in range(rays):
        angle = 2 * math.pi * i / rays
        ux, uy = math.cos(angle), math.sin(angle)
        # how far this field reaches in this direction
        reach = max((p[0] - cx) * ux + (p[1] - cy) * uy for p in points)
        reach = max(reach, 0) + padding
        ring.append((cx + reach * ux, cy + reach * uy))

    # smooth the outline so it reads as a region rather than a polygon
    smoothed = []
    for i in range(rays):
        a, b, c = ring[i - 1], ring[i], ring[(i + 1) % rays]
        smoothed.append(((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4))

    path = "M %.1f %.1f " % smoothed[0]
    for i in range(1, len(smoothed) + 1):
        p0 = smoothed[i - 1]
        p1 = smoothed[i % len(smoothed)]
        path += "Q %.1f %.1f %.1f %.1f " % (p0[0], p0[1],
                                            (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    return path + "Z"


def spokes(members, positions, centres):
    """One line from each person to each field they work in, in its colour."""
    out = []
    for name in sorted(positions):
        for key in members.get(name, []):
            if key in centres:
                out.append((positions[name], centres[key], key, name))
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

    members = {k: v for k, v in members.items() if k in people}
    centres, positions = place(fields, members)

    # The viewBox is fitted to what was actually drawn rather than assumed:
    # a field sitting at the top of the ellipse puts its name above y=0, and a
    # fixed box would clip it.
    half_widths = {f["key"]: label_half_width(f) for f in fields}
    labels = place_labels(fields, centres, positions)
    relax(positions, labels, half_widths, members, centres)
    nudge_labels(labels, centres, positions, half_widths)


    xs = [p[0] for p in positions.values()] + [p[0] for p in labels.values()]
    ys = [p[1] for p in positions.values()] + [p[1] for p in labels.values()]
    pad_node, pad_label = NODE_RADIUS + 26, 140  # node plus its name; label half-width
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
        # Chip widths, one per language since only one is ever showing. Counted
        # per character rather than by length: 자연과학·공학 is seven characters
        # but the interpunct is a third the width of the rest, and treating
        # them alike drew a box half again wider than the name inside it.
        w_ko = text_width(field.get("name", "")) + CHIP_PAD
        w_en = text_width(field.get("name_en", "")) + CHIP_PAD
        lines += ['  - key: "%s"' % field["key"],
                  '    color: "%s"' % field.get("color", "#55703c"),
                  '    chip: "%s"' % chip_colour(field.get("color", "#55703c")),
                  '    glow: "%s"' % glow_colour(field.get("color", "#55703c")),
                  "    w_ko: %.1f" % w_ko, "    w_en: %.1f" % w_en,
                  "    chip_h: %d" % (LABEL_HALF_H * 2 + 14),
                  "    label_x: %.1f" % lx, "    label_y: %.1f" % ly,
                  '    name: "%s"' % field.get("name", field["key"]),
                  '    name_en: "%s"' % field.get("name_en", field.get("name", field["key"])),
                  "    x: %.1f" % x, "    y: %.1f" % y]

    lines += ["", "territories:"]
    for field in fields:
        key = field["key"]
        pts = [positions[n] for n, keys in members.items()
               if key in keys and n in positions]
        if not pts:
            continue
        lines += ['  - key: "%s"' % key, '    d: "%s"' % territory(pts + [centres[key]])]

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
                  '    color: "%s"' % colour_of(fields, members.get(name, [None])[0]),
                  '    color2: "%s"' % (colour_of(fields, members[name][1])
                                        if len(members.get(name, [])) > 1 else ""),
                  "    x: %.1f" % x, "    y: %.1f" % y]

    lines += ["", "edges:"]  # each carries who it belongs to, for hover
    for (ax, ay), (bx, by), key, who in spokes(members, positions, centres):
        lines += ["  - x1: %.1f" % ax, "    y1: %.1f" % ay,
                  "    x2: %.1f" % bx, "    y2: %.1f" % by,
                  '    color: "%s"' % colour_of(fields, key),
                  '    person: "%s"' % re.sub(r"[^a-z0-9]+", "-",
                                              people[who].get("name_en", who).lower()).strip("-")]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote %s: %d nodes, %d fields" % (OUT_PATH, len(positions), len(fields)))


if __name__ == "__main__":
    main()
