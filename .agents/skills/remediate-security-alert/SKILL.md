---
name: remediate-security-alert
description: Use when handling one GitHub security alert (Dependabot, code scanning, or secret scanning) in marlow-lettings, given its alert number. Triage the alert and, if it's real, open a single [sec-auto] PR that fixes it while following AGENTS.md.
---

# Remediate a security alert

Input: one GitHub security alert number.

Follow AGENTS.md throughout.

## Steps

1. Read the alert through the GitHub API: rule or advisory, severity, file and line, and the fix version if there is one
2. Check capacity. Count open PRs authored by any bot (Dependabot, scanners, agents) or titled [sec-auto]. If there are 3 or more, record the alert as queued.
3. Triage before touching code. Decide whether to fix it or skip it with a written reason, for example: it's not reachable in production, it's dev-only, the fix would require editing vendor/, or there is no safe fix. If the fix touches migrations/, request Rafael on the PR and say why. Follow the repo's CONTRIBUTING.md rules and the AGENTS.md entries.
4. Fix it with the smallest change that resolves the alert, one alert per PR
5. Verify beyond CI. Run black --check . and pytest -q. Also exercise every route or job the change touches, and compare /api response before and after. Add a test that fails before the fix and passes after, where one is possible
6. Open the PR with the title [sec-auto] <short description>, linking the alert. The body covers what changed, how it was verified, and the risk.
7. Record the outcome in a GitHub issue for that alert, labeled sec-auto, with the alert, the decision (fixed, skipped or queued), the reason, the PR link, and CI status. Update the issue if it already exists instead of creating a duplicate. Always do this record step, even when you stop early.
8. Never merge, dismiss, or edit vendor/.
