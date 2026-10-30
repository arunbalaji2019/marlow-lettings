---
name: remediate-security-alert
description: Use when handling a GitHub security alert in marlow-lettings, given either a Dependabot package name or a code-scanning / secret-scanning alert number. Triage it and, if it's real, open a single [sec-auto] PR that fixes it while following AGENTS.md.
---

# Remediate a security alert

**Highest priority:** This skill runs unattended. Never wait for approval or ask questions. Commit, push, and open the PR yourself; the human review happens on the PR. If you're blocked, record the alert as "needs human" with the reason and stop.

Input, one of:

- A Dependabot package name (for example `urllib3`). One PR covers all of that package's open alerts.
- A code-scanning or secret-scanning alert number. These stay one alert per PR.

Follow AGENTS.md throughout.

## Steps

1. Read the alerts through the GitHub API.
   - Package: find all its open Dependabot alerts in both manifests (`requirements.txt` and `requirements-dev.txt`; match the package name case-insensitively). For each one note the alert number, advisory, severity, manifest, vulnerable range and first patched version. The target is the lowest version that fixes all of them: the highest first patched version, checked against every vulnerable range.
   - No patched version: if an advisory has no first patched version, leave it out of the target calculation. Fix the package's other alerts as normal, and record the unpatched one as "needs human" with the advisory link and "no patched version available".
   - Alert number: rule or advisory, severity, file and line, and the fix version if there is one.
2. Package only: before starting, check whether an open PR already covers this package. A PR counts as covering it only if its version is at or above the step 1 target, meaning it fixes every open alert for the package.
   - If an open PR covers it, record it as "Covered by PR #N" and stop.
   - If an open [sec-auto] PR touches the package but falls short of the target, update that PR's branch to the target and add the extra alert numbers to its body and record, instead of opening a new PR.
   - If an open PR that isn't [sec-auto] touches the package but falls short of the target, record "needs human" and don't touch it.
3. Check capacity. Count open PRs authored by any bot (Dependabot, scanners, agents) or titled [sec-auto]. If there are 3 or more, record the alert as queued.
4. Triage before touching code. Decide whether to fix it or skip it with a written reason, for example: it's not reachable in production, it's dev-only, the fix would require editing vendor/, or there is no safe fix. If the fix touches migrations/, request Rafael on the PR and say why. Follow the repo's CONTRIBUTING.md rules and the AGENTS.md entries.
5. Fix it with the smallest change that resolves it.
   - Package: upgrade to the target version from step 1 in every manifest that pins it. If the target version requires newer versions of other pinned packages, bump those too, only as far as required, and list each one in the PR body.
   - Include any code changes the upgrade requires (for example, renamed or removed arguments) in the same PR, and list each one in the PR body.
   - Alert number: one alert per PR.
6. Verify beyond CI. Run black --check . and pytest -q. Also exercise every route or job the change touches, and compare /api response before and after. For job code like `marlow/landlord_sync.py`, run the job in dry run mode (`DRY_RUN=1 python -m marlow.landlord_sync`), not just the tests. Add a test that fails before the fix and passes after, where one is possible
7. Open the PR with the title [sec-auto] <short description>, linking the alert. For a package, link every alert number it closes. The body covers what changed, how it was verified, and the risk.
8. Record the outcome in a GitHub issue for that alert or package, labeled sec-auto, with the alert (for a package, every alert number it closes), the decision (fixed, skipped, queued, needs human, or covered by PR #N), the reason, the PR link, and CI status. Update the issue if it already exists instead of creating a duplicate. Always do this record step, even when you stop early.
9. Never merge, dismiss, or edit vendor/.
