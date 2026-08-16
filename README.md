# 동아시아학제연구회 (EAST Research Group)

East Asian Studies & Transdisciplinary Research Group.

Group site, built with Jekyll. The group is made up of scholarship
recipients of the
[Korea Foundation for Advanced Studies](https://www.kfas.or.kr) across a
range of disciplines; the palette (indigo-navy, forest green) and the
tree mark follow from that. Typefaces are
Pretendard (body/UI) and Nanum Myeongjo (headings). The banner image
is a placeholder (Jeong Seon's public-domain 인왕제색도) — swap it for
a real photo whenever there is one, via `assets/images/inwang-jesaekdo.jpg`
in `_includes/header.html`.

## Bilingual content (KO/EN toggle)

The site has a KO/EN toggle in the header (top right, persists via
`localStorage`). It covers all site chrome automatically. For your
own content (posts, seminar entries), it's opt-in per file — add the
`_en` front matter fields below and they'll show up when a reader
switches to English. If you skip them, the Korean version is shown
in both languages, which is a safe fallback, not a bug.

## Adding a news post

Add a markdown file to `_posts/` named `YYYY-MM-DD-title.md`:

```markdown
---
layout: post
title: "제목"
title_en: "Optional English title"
excerpt_en: "Optional English excerpt, used on the homepage list."
content_en: |
  Optional English body. Written as its own markdown block here,
  separate from the Korean body below the front matter.
---

한국어 본문...
```

## Adding a seminar (발제) entry

Add a markdown file to `_seminar/` named `YYYY-MM-DD-title.md`. Same
front matter pattern as posts, plus presenter and cycle fields:

```markdown
---
layout: seminar-entry
title: "제목"
title_en: "Optional English title"
date: 2026-08-11
presenter: "이름"
presenter_en: "Optional romanised name"
cycle: "동아시아와 기억"
cycle_en: "East Asia and Memory"
excerpt_en: "Optional English excerpt."
content_en: |
  Optional English body.
---

한국어 본문...
```

Entries with no write-up carry `sitemap: false`, which also emits
`noindex` — a title and a date is not worth a search result. Delete that
line when you add a summary.

`cycle` is the 대주제 the session belonged to and `cycle_no` its number.
The seminar page groups entries into one section per cycle, newest cycle
first and newest session first within it, so `cycle_no` is what orders
those sections — set it on every entry or the cycle lands in its own
stray group.

The body may be left empty — entries with no write-up yet render a
"요약 준비 중" note instead of a blank page, so sessions can be recorded
before anyone has written them up.

## Pages

`/about/` carries the group's introduction, signed by the leader
(`leader_name` / `leader_photo` in `_config.yml`). The home page keeps a
short version and links through. The margin links on both pages come from
`_data/home_links.yml`.

## Adding people

Members live in `_data/people.yml`; `people.html` just loops over it.
That file is generated from the Google Form survey export, so the
reproducible path is to re-run the importer against a fresh export
rather than hand-editing the YAML:

```bash
python3 tools/import_people.py ~/Downloads/<survey export>.xlsx
git diff _data/people.yml   # read the diff before committing
```

Someone who replied after the export goes in `_data/people_pending.yml`
using the same keys; the importer merges them in and sorts everything
가나다순. Delete the entry once they appear in an export — the export wins
on a name collision either way. Pending entries carry `photo_drive_id`,
which `fetch_photos.py` uses in place of the export's photo column.

Members are sorted 가나다순 in the file itself, so the rendered order does
not depend on who answered the form first, and both languages show the
same order.

Fields of study are normalised too: a leading "Department of" is dropped
and the rest Title Cased, so "Department of History" and "Historical
studies" end up in the same shape.

Romanised names are normalised on import: Title Case, and reordered to
given-name-first by matching a token against romanisations of the Korean
surname. Nothing is respelled, so 이용우 stays "Yi" while 이나현 stays "Lee";
a name whose surname cannot be matched is left exactly as typed.

Per-member keys: `name`, `name_en`, `affiliation`, `affiliation_en`,
`field`, `field_en`, `email`, `bio`, `bio_en`, `link`, `link_label`.
Only `name` is required; the `_en` fields fall back to the Korean ones.
A blank line inside `bio` renders as a paragraph break —
`tools/paragraph_bios.py` adds those to the longer bios, and the importer
keeps them across re-imports as long as the wording itself is unchanged.
The name doubles as the `mailto:` link rather than printing the address,
and `link_label` is a platform name (LinkedIn, Notion, …) that the
importer derives from the URL's host, falling back to the bare domain.

### Member photos

Photos live in `assets/images/people/`, mapped to members by
`_data/people_photos.yml`. A member with no entry there gets an empty
frame, so the page never breaks on a missing photo.

They are fetched from the survey's Drive folder, which has to be shared
as "anyone with the link":

```bash
python3 tools/fetch_photos.py ~/Downloads/<survey export>.xlsx <drive folder url>
```

The photos are matched to members by Drive file ID rather than by
filename, since uploads are named whatever the member's phone called
them. Each is downscaled to 480px and converted to JPEG — they display
at 200px square, and the PNG originals cost several times the size for
no visible gain. A landscape upload where the subject is off to one side
can be reframed via the `CROPS` table in that script.

Photos are kept in their own data file on purpose: `import_people.py`
rewrites `_data/people.yml` wholesale, so anything hand-curated has to
live where the importer can't reach it. Filenames must not start with
an underscore — Jekyll skips those, so the card would point at a file
that never gets published.

## Adding gallery photos

Put the image in `assets/images/gallery/` and add an entry to
`_data/gallery.yml`; the page lists them newest first and shows a
"모으는 중" note while the file is empty. Photos of people other than
whoever is posting need their consent first — unlike the profile
photos, nobody submitted these of themselves.

## Favicon and link preview

`tools/make_images.py` draws both as HTML and screenshots them with
headless Chrome, so they use the site's own tree mark, palette and
typeface:

```bash
python3 tools/make_images.py   # favicon-32, apple-touch-icon, og-cover.jpg
```

The preview card is wired up through `defaults` in `_config.yml` rather
than a top-level `image:` key, because jekyll-seo-tag only reads
`page.image` and ignores `site.image`.

## Local development

```bash
bundle install
bundle exec jekyll serve
```

Then open http://127.0.0.1:4000/.

## Deployment

Lives at [eastresearch.github.io](https://eastresearch.github.io/)
via the `eastresearch` GitHub org's special `<org>.github.io` repo. Pushing to `main` triggers `.github/workflows/pages.yml`, which
builds the site and deploys it via GitHub Actions. In the repo's
**Settings → Pages**, the source is set to **GitHub Actions**.
