# Contributing

## Rules for every PR

1. CI must be green (black + pytest).
2. At least one human review. Nothing merges automatically, including bot PRs.
3. Keep PRs small. One concern per PR.

## Areas with extra rules

- **`vendor/`** is synced from upstream (see `vendor/floorplan/VENDORED.md`).
  Never edit it here; local edits are overwritten on the next sync. Fixes go
  upstream, and we bump the vendored copy.
- **`migrations/`** changes need the data team (Rafael) on the review.
- **Public API responses** (`/api/...`) are parsed by the mobile app. App v3 is
  still on ~30% of devices and can't be force-updated, so response field names
  and types must not change without a versioned endpoint.

## Bots

Automated PRs (Dependabot, scanners, agents) must:

- have a title starting with `[sec-auto]`
- link the alert or advisory they address
- not exceed 3 open at a time. Reviewers ignore anything beyond that.
