#!/usr/bin/env python3
"""Render the favicon and the link-preview (og:image) card.

Both are drawn as HTML and screenshotted with headless Chrome, so they use the
same tree mark, palette and typeface as the banner rather than being traced by
hand in an image editor. Re-run after changing the palette or the banner.

    python3 tools/make_images.py

Writes assets/favicon-32.png, assets/apple-touch-icon.png and
assets/images/og-cover.jpg.
"""

import os
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAVY_DARK = "#21234f"
SEAL_CREAM = "#f3ead4"
SEAL_GREEN = "#cfe0bd"

MARK_HTML = """<!doctype html><meta charset="utf-8">
<style>
  html, body { margin: 0; width: %(size)spx; height: %(size)spx; }
  body {
    background: %(navy)s;
    display: flex; align-items: center; justify-content: center;
  }
  .mark { font-size: %(font)spx; line-height: 1; }
</style>
<div class="mark">🌳</div>
"""

OG_HTML = """<!doctype html><meta charset="utf-8">
<style>
  html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; }
  .wrap { position: relative; width: 1200px; height: 630px; }
  .wrap img {
    width: 100%%; height: 100%%; object-fit: cover; object-position: center 32%%;
    display: block;
  }
  .veil {
    position: absolute; inset: 0;
    background: linear-gradient(to top,
      rgba(33,35,79,0.94) 0%%, rgba(33,35,79,0.62) 45%%, rgba(33,35,79,0.12) 100%%);
    display: flex; align-items: flex-end;
  }
  .inner { padding: 0 72px 68px; display: flex; align-items: center; gap: 28px; }
  .mark { font-size: 76px; line-height: 1; flex: 0 0 auto; }
  h1 {
    font-family: "Nanum Myeongjo", "Apple SD Gothic Neo", serif;
    font-size: 76px; font-weight: 800; color: #fff; margin: 0 0 6px;
    letter-spacing: -0.01em;
  }
  p {
    font-family: "Nanum Myeongjo", "Apple SD Gothic Neo", serif;
    font-size: 27px; color: %(green)s; margin: 0;
  }
</style>
<div class="wrap">
  <img src="file://%(painting)s" alt="">
  <div class="veil"><div class="inner">
    <div class="mark">🌳</div>
    <div>
      <h1>동아시아학제연구회</h1>
      <p>East Asian Interdisciplinary Studies Group</p>
    </div>
  </div></div>
</div>
"""


def shoot(html, out_png, width, height):
    """Render an HTML string to a PNG of exactly width x height."""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        page = f.name
    try:
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--default-background-color=00000000",
                        "--force-device-scale-factor=1",
                        "--window-size=%d,%d" % (width, height),
                        "--virtual-time-budget=3000",
                        "--screenshot=" + out_png, "file://" + page],
                       check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.remove(page)


def main():
    if not os.path.exists(CHROME):
        sys.exit("headless Chrome not found at %s" % CHROME)
    os.chdir(ROOT)

    for size, font, name in [
        (180, 116, "assets/apple-touch-icon.png"),
        (32, 21, "assets/favicon-32.png"),
    ]:
        shoot(MARK_HTML % {"size": size, "font": font, "navy": NAVY_DARK},
              name, size, size)
        print("wrote", name)

    painting = os.path.join(ROOT, "assets/images/inwang-jesaekdo.jpg")
    shoot(OG_HTML % {"painting": painting, "green": SEAL_GREEN, "cream": SEAL_CREAM},
          "/tmp/og-cover.png", 1200, 630)
    # JPEG keeps the card well under the ~1MB that chat apps will fetch
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82",
                    "/tmp/og-cover.png", "--out", "assets/images/og-cover.jpg"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote assets/images/og-cover.jpg")


if __name__ == "__main__":
    main()
