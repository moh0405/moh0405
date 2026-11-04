# Profile activity cards

The README embeds SVG files committed to this repository. Visitors do not depend on a third-party stats server being available.

## Refreshing

The **Refresh profile stats** GitHub Actions workflow runs daily at 06:23 UTC. To update immediately, open **Actions → Refresh profile stats → Run workflow**. It also runs when its workflow or Python generator changes on `main`.

The workflow uses its built-in `GITHUB_TOKEN` with `contents: write` to read GitHub activity and commit `assets/metrics.svg` and `assets/activity.svg`. No personal access token, external account, or Python package is required. If fetching or rendering fails, existing cards stay in place. The last successful update date appears on the metrics card.

## What the numbers mean

- **Commit contributions:** GitHub's `totalCommitContributions` for the displayed period, following its contribution rules. This is not an all-time count of every commit on every branch.
- **Total contributions:** GitHub's contribution calendar total, which also includes activity such as issues, pull requests, and reviews.
- **Pull requests opened / code reviews:** contribution counts for the same period.
- **Days with activity:** calendar dates with at least one contribution.
- **Longest streak:** consecutive active calendar dates inside the displayed period.

All cards cover 365 inclusive UTC calendar dates through the time of the refresh. Data is limited to what GitHub exposes to the workflow token. Do not expect a complete private-repository commit breakdown. Private repository names, source code, and credentials are never written into the cards.

## Editing the design

`assets/header.svg` is the static banner. `scripts/profile_stats.py` controls the card colors, typography, layout, and contribution calendar. It uses only the Python standard library.

To regenerate locally with an appropriately scoped GitHub token available in your environment:

```sh
PROFILE_LOGIN=moh0405 python3 scripts/profile_stats.py
```

Set `GH_TOKEN` in your shell environment first; do not commit it to this repository.
