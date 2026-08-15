# 동아시아학제연구모임 (East Asia Interdisciplinary Studies Group)

Group site, built with Jekyll. Palette (indigo-navy, forest green,
bronze) and the 林 seal mark nod to
[문우림 (文友林, Forest of Learning)](https://cvt.kfas.or.kr/intro/type1.php),
the KFAS program this group's members met through. Typefaces are
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

`cycle` is the 대주제 the session belonged to, shown as a tag on the
seminar list and entry pages. The body may be left empty — entries with
no write-up yet render a "요약 준비 중" note instead of a blank page, so
sessions can be recorded before anyone has written them up.

## Adding people

Members live in `_data/people.yml`; `people.html` just loops over it.
That file is generated from the Google Form survey export, so the
reproducible path is to re-run the importer against a fresh export
rather than hand-editing the YAML:

```bash
python3 tools/import_people.py ~/Downloads/<survey export>.xlsx
git diff _data/people.yml   # read the diff before committing
```

Per-member keys: `name`, `name_en`, `affiliation`, `affiliation_en`,
`field`, `field_en`, `email`, `bio`, `bio_en`, `link`, `link_label`.
Only `name` is required; the `_en` fields fall back to the Korean ones.
The name doubles as the `mailto:` link rather than printing the address,
and `link_label` is a platform name (LinkedIn, Notion, …) that the
importer derives from the URL's host, falling back to the bare domain.

### Member photos

Cards have a photo slot that currently renders an empty frame, because
the survey collected photos as Google Drive links that require sign-in
and so can't be fetched automatically. To fill it in:

1. Download the photos from the survey's Drive links while signed in.
2. Commit them to `assets/images/people/`. Filenames must not start
   with an underscore — Jekyll skips those.
3. Uncomment the matching line in `_data/people_photos.yml`, which maps
   a member's Korean name to their filename.

Photos are kept in their own data file on purpose: `import_people.py`
rewrites `_data/people.yml` wholesale, so anything hand-curated has to
live where the importer can't reach it.

## Local development

```bash
bundle install
bundle exec jekyll serve
```

Then open http://127.0.0.1:4000/.

## Deployment

Lives at [eastasia-interdisciplinary.github.io](https://eastasia-interdisciplinary.github.io/)
via the `eastasia-interdisciplinary` GitHub org's special `<org>.github.io`
repo. Pushing to `main` triggers `.github/workflows/pages.yml`, which
builds the site and deploys it via GitHub Actions. In the repo's
**Settings → Pages**, the source is set to **GitHub Actions**.
