# zgxsin.github.io

Personal website and technical blog (robotics, perception, SLAM, ML), built with Jekyll 4
and served at https://www.guoxiang-zhou.xyz.

## Build and deploy

- `.github/workflows/pages.yml` builds with this repo's `Gemfile` and deploys to GitHub
  Pages on every push to `master` (Settings > Pages > Source: GitHub Actions). The local
  build and the live site are therefore identical. Do not add the `github-pages` gem back.
- Local preview: `bundle exec jekyll serve --livereload`. Add `--future` for posts dated
  after today (Jekyll skips them otherwise, also on the live site) and `--drafts` for
  `_drafts/`.
- `published: false` in front matter hides a post everywhere.

## Writing a post

- File: `_posts/YYYY-MM-DD-slug.md`. The URL is `/YYYY/MM/DD/slug/`; changing the date or
  slug breaks existing links, so do not rename published posts.
- Front matter: `title`, `date`, `author: zgxsin`, `published: true`. Optional
  `image: /assets/images/posts/<slug>/cover.png` sets the social preview image.
- Start with `* TOC` + `{:toc}` on the next line; the layout turns it into the side panel.
- Math: `$...$` inline and `$$...$$` display (MathJax 4, client-side). Escape `_` and `*`
  inside inline math with a backslash when kramdown would read them as emphasis
  (`\mathbf{p}\_1`). Use `\lbrace \rbrace` instead of `\{ \}`.
- Never write `{{` or `{%` in prose or code blocks; Liquid evaluates them. Wrap such code in
  `{% raw %}...{% endraw %}`.
- Link other posts by URL path, e.g. `[Kalman filter](/2026/11/04/kalman-filter/)`.
- Style: direct, technical, no em dashes, no emoji.

## Visuals

Pick the lightest tool that shows the idea:

| Need | Tool |
| --- | --- |
| Flowchart, pipeline, node graph, sequence, state machine | ```` ```mermaid ```` block |
| Precise geometric diagram, annotated schematic | Static SVG figure in `_includes/figures/` |
| Concept that becomes clear by changing a parameter | Interactive SVG figure (slider, buttons) |
| Screenshot, photo, plot exported from Python | `{% include image.html %}` |

### Mermaid

Fenced ```` ```mermaid ```` blocks render client-side (`_layouts/post.html`), themed to the
site palette. Quote node labels that contain punctuation: `A["Encoder<br/>resize"]`.

### SVG figures

- Start from `_includes/figures/_template.html`. Copy it to
  `_includes/figures/<name>.html` and replace the prefix `xyz` with a short unique one.
- Include it with `{% include figures/<name>.html %}`, optionally with
  `caption="Markdown caption."`.
- Shared classes and colors are in `_sass/_figures.scss`. The root is
  `<figure id="..." class="fig xyz">`, with `fig-svg`, `fig-legend`, `fig-control` and
  `fig-buttons` as needed. The figure's own `<style>` holds only figure-specific rules,
  all prefixed `.xyz-`. Element ids are prefixed too, since several figures share a page.
- Colors: the `--fig-*` tokens (Primer: text `#24292e`, muted `#586069`, border `#d0d7de`,
  blue `#0366d6`, green `#22863a`, red `#d73a49`, purple `#6f42c1`, orange `#e36209`). SVG
  presentation attributes cannot use `var()`, so write the hex value there and use the
  tokens in CSS.
- Text: 13px default, 12px for notes. Design for a 760px-wide `viewBox` (the reading
  column). Any `viewBox` wider than 600 needs `fig-svg-wide`, which keeps the figure
  readable on phones by scrolling it sideways instead of shrinking the text. Figures
  that compute their `viewBox` from the rendered width in JS do not need it.
- Every `<svg>` gets `role="img"` and an `aria-label` that states what the figure shows.
- Scripts are inline, wrapped in an IIFE, with no external libraries.
- `class="fig fig-wide"` breaks out of the reading column to the 960px page width.
- Check at desktop width and at 390px before publishing, e.g. with headless Chrome:
  `google-chrome --headless=new --window-size=390,2000 --screenshot=out.png <url>`.

### Images

- Store per post in `assets/images/posts/<slug>/`. Use SVG for diagrams (Excalidraw,
  draw.io), WebP or JPEG for photos and screenshots, and keep each file under about 300 KB.
- `{% include image.html src="/assets/images/posts/<slug>/x.svg" alt="..." caption="..." %}`
  adds lazy loading and a caption. Optional `width="480px"` and `wide=true`.
- Always write meaningful `alt` text.

## Known issues

- 39 images in seven 2020 posts imported from WordPress were lost (no backup, no Wayback
  snapshot). They are marked `<!-- Image lost in the WordPress migration: uploads/... -->`
  in place, so they can be restored if the files turn up.
