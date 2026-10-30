# AGENTS.md

House rules for automated agents working in this repo. Source of truth: CONTRIBUTING.md.

## Pull requests

- Start every PR title with `[sec-auto]`.
- Link the alert or advisory the PR addresses in the PR description.
- Never have more than 3 open bot PRs at a time. If 3 are open, stop and do not open another.
- One concern per PR. Keep it small.
- CI must be green (`black --check .` and `pytest -q`) before asking for review.

## Never

- Never merge a PR. A human reviews and merges every PR, including yours.
- Never dismiss, close, or change the state of a security alert. Humans triage alerts.
- Never edit anything under `vendor/`. It is synced from upstream and local edits get overwritten. Fixes go upstream (see `vendor/floorplan/VENDORED.md`).
- Never change `/api/...` response field names or types. The mobile app (v3 is still on about 30% of devices) parses them. A breaking change needs a new versioned endpoint.

## Needs a specific reviewer

- Any change under `migrations/` must have Rafael (data team) on the review. Request him and say so in the PR description.
