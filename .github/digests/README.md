# Scheduled digests

Each folder under `profiles/` defines a digest. Its `profile.json` sets the post slug, title, category, quiet-day wording, video alt text, feed URLs, and case-insensitive regular expressions for matching feed entries. Its `prompt.md` defines how to select and summarize updates.

Sources can use a plain RSS or Atom URL, or an object with a `url`, optional `format` (`xml`, `json-feed`, or `smartrecruiters`), and optional `lookback_days` to override the profile's window. The profile's `lookback_days` defaults to three. Set `include_readiness` to `false` to use the profile's own layout without readiness ratings. Set `link_titles` to `true` to link story titles to their source pages.

To add a topic, copy a profile folder and update those files. Use a unique post slug and register the category in [`_data/categories.yml`](../../_data/categories.yml). Copy a [scheduled workflow](../workflows/robotics-data-infrastructure-digest.yml), set its schedule and concurrency group, and pass the new folder name as `profile`. The [shared workflow](../workflows/publish-digest.yml) handles generation and publishing. Pass `review: true` to use the shared [review prompt](review-prompt.md) and [revision prompt](revision-prompt.md).

For profiles with AI review enabled, each review gets only the draft it is judging and its source excerpts. The reviewer classifies material issues using a fixed set of lesson IDs. GitHub Actions saves newly learned IDs in that profile's `learned-rules.json`, and future runs add the matching rules to the drafting prompt. If a revised draft fails review, the workflow can still save the lessons while withholding the draft.

The generator starts with `gemini-4-hydrogen` or the configured `DIGEST_MODEL`. If it hits a rate limit or still gets a server error after retries, it tries `gemini-3.8-flash` and then `gemini-3.1-flash-lite`. Both backups use the same `GEMINI_API_KEY` and are available on Google's free tier, subject to project eligibility and usage limits. Once a backup succeeds, the remaining requests for that edition start with that model. The post credits the model that wrote the published draft unless `DIGEST_AUTHOR` is set.

Run a feed check from the repository root without calling Gemini or writing a post.

```sh
python3 .github/digests/generate.py robotics-data-infrastructure --sources-only
```
