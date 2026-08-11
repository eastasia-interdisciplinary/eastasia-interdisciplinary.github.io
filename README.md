# 동아시아학제연구모임 (East Asia Interdisciplinary Studies Group)

Group site, built with Jekyll. Color palette and lineage badge nod to
[문우림 (Munwoorim)](https://cvt.kfas.or.kr/intro/type1.php), the KFAS
program this group grew out of. Layout is modeled loosely on the
[Geneva Symmetry Group](https://genevasymmetrygroup.wordpress.com/) site
(nav bar, news feed, sidebar).

## Adding a news post

Add a markdown file to `_posts/` named `YYYY-MM-DD-title.md`:

```markdown
---
layout: post
title: "제목"
---

내용...
```

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
**Settings → Pages**, set the source to **GitHub Actions**.
