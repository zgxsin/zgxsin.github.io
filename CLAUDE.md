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
- Front matter: `title`, `date`, `author: "Guoxiang (Shawn) Zhou"`, `published: true`,
  `categories: [technology]`. Category slugs must be listed in `_data/categories.yml`
  (technology, life, finance); add new ones there. They drive the filter on the Blogs page
  and the label on each post, and are not part of the URL. Optional
  `image: /assets/images/posts/<slug>/cover.png` sets the social preview image.
- Start with `* TOC` + `{:toc}` on the next line; the layout turns it into the side panel.
- Heading levels follow the content logic: `##` for top-level sections (never `#`, which is
  the post title), `###` for topics within a section, `####` for a topic that belongs to the
  one above it (a variant, a failure mode and its fix, a stage of a process). Avoid long runs
  of sibling headings; group related ones under a parent. Heading text sets the anchor, so
  changing levels is safe but renaming a heading breaks `#links` to it.
- Math: `$...$` inline and `$$...$$` display (MathJax 4, client-side). Escape `_` and `*`
  inside inline math with a backslash when kramdown would read them as emphasis
  (`\mathbf{p}\_1`). Do not escape inside `$$` display blocks: kramdown passes them through
  verbatim and MathJax renders `\_` as a literal underscore. Use `\lbrace \rbrace` instead of `\{ \}`.
- Never write `{{` or `{%` in prose or code blocks; Liquid evaluates them. Wrap such code in
  `{% raw %}...{% endraw %}`.
- Link other posts by URL path, e.g. `[Kalman filter](/2024/12/15/kalman-filter/)`.
- Write out the full name at the first mention of every abbreviation, followed by the
  abbreviation in parentheses: "reinforcement learning (RL)", then "RL" afterwards. This
  covers prose, lists and tables, including common ones (GPU, ROS, LiDAR). Product and
  brand names (NVIDIA, PhysX, RTX) are not abbreviations. Short labels inside Mermaid
  diagrams and figures may use the abbreviation, and headings should avoid one that the
  text has not yet defined.
- Every entry in a References section links its title to the source: the arXiv abstract
  page (`https://arxiv.org/abs/<id>`) when one exists, otherwise the DOI
  (`https://doi.org/<doi>`) or the official project page. Check that each link resolves to
  the cited paper before publishing.
- Style: direct, technical, no em dashes, no emoji.

## Visuals

Add a diagram or visual wherever it makes a concept easier to understand than prose
alone: a pipeline or data flow, geometry, a trade-off controlled by a parameter, a
comparison, a decision. Each one should explain something the text cannot show as well;
skip decorative figures.

Prefer SVG figures in `_includes/figures/` for diagrams and visuals: they control font
size and layout, match the site palette, and stay readable on phones. Use Mermaid only for
small diagrams (roughly up to six nodes in a single chain, no wide fan-out), where its
automatic layout still renders at a readable size.

| Need | Tool |
| --- | --- |
| Flowchart, pipeline, decision tree, architecture, annotated schematic | Static SVG figure in `_includes/figures/` |
| Concept that becomes clear by changing a parameter | Interactive SVG figure (slider, buttons) |
| Small linear flow or loop, a few nodes | ```` ```mermaid ```` block |
| Screenshot, photo, plot exported from Python | `{% include image.html %}` |
| Robot demo, animation, screen recording, talk | `{% include video.html %}` |

### Mermaid

Fenced ```` ```mermaid ```` blocks render client-side (`_layouts/post.html`), themed to the
site palette. Quote node labels that contain punctuation: `A["Encoder<br/>resize"]`.
Do not start a label with `+ `, `- `, `* ` or `1. `: Mermaid parses it as a Markdown list
and renders "Unsupported markdown: list".

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

### Videos

- Short clips (demos, animations, up to about 10 s, no sound) go in
  `assets/videos/posts/<slug>/` as MP4 (H.264, `-movflags +faststart`) or WebM, under
  about 5 MB, plus a JPEG/WebP poster frame next to the post's images. Never commit GIFs;
  convert them to MP4. Git keeps every version forever, so re-export sparingly.
- `{% include video.html src="/assets/videos/posts/<slug>/clip.mp4" poster="/assets/images/posts/<slug>/clip.jpg" alt="..." caption="..." %}`
  plays like a GIF: muted, looped, only while on screen. Users with reduced motion get
  controls instead. Add `loop=false` for a normal video with controls.
- Anything long or with sound goes on YouTube:
  `{% include video.html youtube="VIDEO_ID" alt="..." caption="..." %}`, optional
  `start=<seconds>`. It shows the thumbnail and loads the youtube-nocookie player only on
  click.
- Both take `width="480px"` and `wide=true`, and `src`/`poster` may be absolute URLs
  (for files hosted outside the repo).
- Encode a clip:
  `ffmpeg -i in.mov -t 10 -vf "scale=1280:-2,fps=30" -an -c:v libx264 -crf 28 -preset slow -pix_fmt yuv420p -movflags +faststart clip.mp4`,
  and the poster: `ffmpeg -i clip.mp4 -frames:v 1 -q:v 3 clip.jpg`.

## Known issues

- 39 images in seven 2020 posts imported from WordPress were lost (no backup, no Wayback
  snapshot). They are marked `<!-- Image lost in the WordPress migration: uploads/... -->`
  in place, so they can be restored if the files turn up.
