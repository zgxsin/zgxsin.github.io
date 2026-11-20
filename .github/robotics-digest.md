# Daily robotics hardware and sensors digest

Create a standalone task in ChatGPT's Scheduled view with GitHub access to `zgxsin/zgxsin.github.io`. Set it to run daily at 08:00 in `Europe/Zurich` and use the prompt below. Each run opens a pull request for review. GitHub Pages publishes the post after the pull request is merged into `master`.

## Scheduled task prompt

> Search the web for recent robotics hardware and sensor updates, including lidar, depth cameras, inertial sensors, tactile sensors, grippers, actuators, and robot platforms. Cover markets, academia, and industry. Start with the last 24 hours and check recent issues for duplicates. For each verified item, give the original date, link to its primary source, and explain what changed and why it matters. Attribute vendor claims and label preprints. Keep quiet-day editions brief.
>
> Use today's date in Europe/Zurich and the Jekyll format of the existing digest posts. Create one Markdown file at `_posts/YYYY-MM-DD-robotics-hardware-and-sensors-digest.md` in `zgxsin/zgxsin.github.io`. Check for the dated post on `master` and for an open pull request for that edition before creating anything. If either exists, report it and stop.
>
> Create a branch named `codex/robotics-digest-YYYY-MM-DD` from `master`, commit only the new post on that branch, and open a pull request targeting `master`. If a previous run left the branch behind, reuse it only if it contains exactly the intended post and no unrelated changes. Do not commit directly to `master` or merge the pull request. Report the pull request link and any build failure.
