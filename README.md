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
front matter pattern as posts, plus an optional `presenter` field:

```markdown
---
layout: seminar-entry
title: "제목"
title_en: "Optional English title"
date: 2026-08-11
presenter: "이름"
excerpt_en: "Optional English excerpt."
content_en: |
  Optional English body.
---

한국어 본문...
```

## Adding people

`people.html` is a plain grid, not a collection — edit it directly.
Copy an existing `.grid-card` block inside `.card-grid` for each new
member.

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
