# AGENTS.md

House rules for automated agents working in this repo. Based on CONTRIBUTING.md.

## Pull requests

- For PRs that fix a security alert: title starts with `[sec-auto]` and links the alert.
- Never have more than 3 open bot or agent PRs. If 3 are open, don't open another; record the alert as queued.
- One concern per PR. Keep it small.
- CI must be green (`black --check .` and `pytest -q`) before asking for review.
- Always do the record step, even when you stop early (step 7 of `.agents/skills/remediate-security-alert/SKILL.md`).

## Never

- Never merge a PR. A human reviews and merges every PR, including yours.
- Never push to main directly.
- Never dismiss, close, or change the state of a security alert. Humans triage alerts.
- Never edit anything under `vendor/`. It is synced from upstream and local edits get overwritten. Fixes go upstream (see `vendor/floorplan/VENDORED.md`).
- Never change `/api/...` response field names or types. The mobile app (v3 is still on about 30% of devices) parses them. A breaking change needs a new versioned endpoint.

## Needs a specific reviewer

- Any change under `migrations/` must have Rafael (data team) on the review. Request him and say so in the PR description.
