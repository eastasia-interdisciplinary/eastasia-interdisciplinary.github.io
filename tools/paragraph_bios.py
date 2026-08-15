#!/usr/bin/env python3
"""Break the longer bios in _data/people.yml into paragraphs.

The survey's bio box is a single free-text field, so most people typed several
hundred characters as one block. Rendered as one paragraph that is a wall of
text, so this inserts paragraph breaks at the points where the subject
actually shifts -- typically background / current research / wider interests.

Wording is never touched, only whitespace: each anchor below is the phrase
that should begin a new paragraph, and the run of whitespace before it becomes
a blank line. tools/import_people.py compares bios with whitespace removed, so
this survives a re-import as long as the person has not rewritten their answer.

    python3 tools/paragraph_bios.py

Safe to re-run: a bio already broken at these anchors is left unchanged.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_people import HEADER, OUT_PATH, emit, read_existing  # noqa: E402

# (name, field): phrases that should each start a new paragraph
BREAKS = {
    ("성민경", "bio"): ["이러한 관점에서", "#불교사"],
    ("성민경", "bio_en"): ["From this perspective,"],
    ("서은교", "bio"): ["사학과에서 한국사를"],
    ("서은교", "bio_en"): ["I major in History,"],
    ("엄윤주", "bio"): ["석사 과정에서는", "박사과정에서는", "아울러 언어 접촉이"],
    ("엄윤주", "bio_en"): ["Her master's thesis", "Doctoral research deepens"],
    ("유하린", "bio_en"): [
        "I am particularly interested in how linguistic",
        "I am also interested in the use of generative AI",
    ],
    ("이나현", "bio"): ["특히 동아시아의"],
    ("이나현", "bio_en"): ["Focusing on East Asia,"],
    ("이용우", "bio"): ["서울대학교 자유전공학부에서", "동아시아의 문화적 유산을"],
    ("이용우", "bio_en"): ["I obtained a B.A.", "I am interested in developing"],
    ("이유경", "bio"): ["주요 논문으로"],
    ("이유경", "bio_en"): ["My major publication is"],
    ("이한석", "bio"): ["이에 두 형제가", "나아가 김창협"],
    ("이한석", "bio_en"): ["I am preparing my doctoral dissertation", "Furthermore, I explore"],
    ("황승혁", "bio"): ["아직 구체적인 연구 분야를"],
    ("황승혁", "bio_en"): ["Although I have not yet decided"],
}


def split_at(text, anchor):
    """Turn the whitespace preceding `anchor` into a paragraph break."""
    at = text.find(anchor)
    if at <= 0:
        raise SystemExit("anchor not found: %r" % anchor)
    start = at
    while start > 0 and text[start - 1] in " \t\n":
        start -= 1
    return text[:start] + "\n\n" + text[at:]


def main():
    entries = read_existing(OUT_PATH)
    if not entries:
        raise SystemExit("no %s to work on -- run import_people.py first" % OUT_PATH)

    changed = 0
    for (name, field), anchors in BREAKS.items():
        if name not in entries:
            raise SystemExit("no such member: %s" % name)
        before = entries[name].get(field, "")
        after = before
        for anchor in anchors:
            after = split_at(after, anchor)
        if after != before:
            entries[name][field] = after
            changed += 1

    out = [HEADER]
    for entry in entries.values():
        out.append("- " + "\n".join(emit(k, v) for k, v in entry.items())[2:])
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out) + "\n")

    total = sum(v.get("bio", "").count("\n\n") + 1 for v in entries.values())
    print("broke %d field(s); %d paragraphs across %d Korean bios"
          % (changed, total, len(entries)))


if __name__ == "__main__":
    main()
