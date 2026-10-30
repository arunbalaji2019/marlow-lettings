# sec-auto engineering reference

This is the engineering reference for sec-auto. For the one-page overview, see
[README-sec-auto.md](../README-sec-auto.md).

sec-auto is how marlow-lettings handles GitHub security alerts with Devin. A
Devin Automation runs on a GitHub webhook and every weekday at 9:00 PT. A preflight script picks the most severe
open alerts that have room for a PR. Each one gets its own Devin session, which
runs the `remediate-security-alert` skill: it triages the alert, opens one small
`[sec-auto]` PR if a fix is safe, and records the outcome in a GitHub issue.
Humans review and merge every PR and triage every alert. Nothing merges or
dismisses anything automatically.

```
trigger  ──▶ preflight.py ──▶ {"items": [...]} ──▶ one Devin session per item
             (off switch,                          │
              capacity,                            ├─ remediate-security-alert skill
              pick top N)                          ├─ [sec-auto] PR  ──▶ human review + merge
                                                   └─ [sec-auto record] <id> issue
```

## The files

| File | What it is | Who reads it |
|---|---|---|
| `CONTRIBUTING.md` | Rules for every PR, human or bot: green CI, a human review, one concern per PR, plus the `vendor/`, `migrations/` and `/api` rules and the bot rules. | Everyone |
| `AGENTS.md` | The same rules restated as house rules for agents. Devin loads it as always-on rules in every session in this repo. | Agents |
| `.agents/skills/remediate-security-alert/SKILL.md` | The step-by-step procedure for one alert or one Dependabot package. | The Devin session each item starts |
| `.agents/automations/preflight.py` | The script the Automation runs before starting sessions. The copy in the repo is the reference; the Automation stores its own pasted copy. | The Automation |

### Rules that apply to every sec-auto PR

From `CONTRIBUTING.md` and `AGENTS.md`:

- **Title:** starts with `[sec-auto]` and links the alert, advisory or issue it addresses.
- **Capacity:** at most 3 open bot or agent PRs (Dependabot, scanners, agents). Reviewers ignore anything past that. If 3 are open, the alert is recorded as queued.
- **Size:** one concern per PR.
- **CI:** `black --check .` and `pytest -q` must pass before review.
- **Never:** merge a PR, push to `main`, dismiss or change the state of a security alert, or edit `vendor/`. `vendor/` is synced from upstream, so fixes go upstream (see `vendor/floorplan/VENDORED.md`).
- **API stability:** never change `/api/...` response field names or types. Mobile app v3 is still on about 30% of devices and parses them. A breaking change needs a new versioned endpoint.
- **Migrations:** any change under `migrations/` needs Rafael (data team) on the review, and the PR says why.
- **Record step:** always record the outcome, even when stopping early.

## How a run works

1. **Trigger.** The Automation fires on either of two triggers: a GitHub repo webhook (the webhook URL carries the Automation's `?secret=`), or a schedule every weekday at 9:00 PT.
2. **Preflight.** `preflight.py` runs on its own short-lived VM, separate from the Devin sessions. It decides which items, if any, to start (details below).
3. **Fan-out.** The script writes `{"items": [...]}`. The Automation starts one Devin session per item and gives each session that item's fields. An empty list starts nothing. Only 1 session runs at a time; up to 10 more wait in the queue.
4. **Dedupe.** The Automation drops an item whose `id` and `version` it has already started, so the same unchanged item never runs twice.
5. **Session.** Each session runs the `remediate-security-alert` skill for its item, with `AGENTS.md` loaded. It runs unattended: it never waits for approval or asks questions. It commits, pushes and opens the PR itself. If it's blocked, it records "needs human" with the reason and stops.
6. **Human review.** A human reviews the PR, and merges it if it's right. The alert closes when Dependabot or CodeQL rescans `main`.

## The preflight script

`.agents/automations/preflight.py` uses the Python standard library only. It
has a 50 second overall budget and a 10 second limit per request, inside the
Automation's 60 second default timeout.

In order, it:

1. **Checks the off switch.** It reads the repo variable `SEC_AUTO_ENABLED`. Anything other than `true`, including a missing variable, writes `{"items": []}` and exits.
2. **Checks capacity.** It counts open PRs whose author is a GitHub Bot account or whose title starts with `[sec-auto]`. Free slots are 3 minus that count. With no free slots it writes `{"items": []}` and exits.
3. **Collects items.**
   - One per open code-scanning alert: `id` `cs-<alert number>`, with its severity, rule and URL. Severity is the rule's security severity. If the rule has none, `error`, `warning` and `note` count as high, medium and low.
   - One per Dependabot package: `id` `dep-<package name lowercased>`. Case variants such as `Werkzeug` and `werkzeug` merge into one item, with all its open alert numbers and its highest severity.
4. **Skips recorded items.** An item that has an open issue titled `[sec-auto record] <id>` is dropped. Without this, an item that stays open after handling (a fix PR not yet merged, or "needs human") would keep its slot forever and nothing below it would run.
5. **Sets each item's `version`** to its sorted alert numbers, then `:`, then the latest `closed_at` of that id's closed record issues, or `0` if there are none. Examples: `3:0`, `2,7,37,39,44,71:0`, `4:2026-10-30T02:00:00Z`. The item runs again when its package gets a new alert or when a human closes its record issue.
6. **Sorts and trims.** It sorts by severity (critical, high, medium, low), then by `id`, keeps the top N where N is the free slots, and writes `{"items": [...]}` to `$OUTPUT_FILE`.

**Failures:** any API error other than the off-switch 404 exits non-zero. A failed preflight starts no sessions, and the Automation emails on failure.

**Off switch, tested live:** with `SEC_AUTO_ENABLED` not set to `true`, a run was skipped in 0.3s and no session started.

**Example item:**
```json
{
  "id": "dep-certifi",
  "version": "2,7,37,39,44,71:0",
  "kind": "dependabot",
  "package": "certifi",
  "alert_numbers": [2, 7, 37, 39, 44, 71],
  "severity": "critical"
}
```

### Test it locally

```
MARLOW_GH_READ=<token> python3 .agents/automations/preflight.py --test
```

`--test` prints the items instead of writing `$OUTPUT_FILE`. It calls the real
GitHub API, so use a token with the permissions below.

## The remediate-security-alert skill

Input is either a Dependabot package name, which gets one PR for all its alerts,
or a code-scanning or secret-scanning alert number, which gets one PR per alert.

1. **Read the alerts.**
   - **Package:** find every open alert for it in `requirements.txt` and `requirements-dev.txt`, matching the name case-insensitively. The target version is the highest first-patched version, checked against every vulnerable range. An advisory with no patched version is left out of the target and recorded as "needs human".
   - **Alert number:** read the rule or advisory, severity, file and line, and the fix version if there is one.
2. **Check for an existing PR (package only).** An open PR at or above the target means "Covered by PR #N", and the skill stops. A `[sec-auto]` PR below the target gets its branch raised to the target. A non-`[sec-auto]` PR below the target is recorded as "needs human" and left alone.
3. **Check capacity.** With 3 or more open bot or agent PRs, the alert is recorded as queued.
4. **Triage before touching code.** Fix it or skip it with a written reason, for example not reachable in production, dev-only, the fix would need `vendor/` edits, or there is no safe fix.
5. **Fix with the smallest change.** For a package, upgrade every manifest that pins it. Bump other pinned packages only as far as the target requires. Include any code changes the upgrade needs, such as renamed or removed arguments. List each bump and code change in the PR body.
6. **Verify beyond CI.**
   - Run `black --check .` and `pytest -q`.
   - Exercise every touched route or job and compare `/api` responses before and after.
   - Run job code like `marlow/landlord_sync.py` in dry-run mode: `DRY_RUN=1 python -m marlow.landlord_sync`.
   - Add a test that fails before the fix and passes after, where one is possible.
7. **Open the PR.** The title is `[sec-auto] <short description>`. The body links every alert it closes and covers what changed, how it was verified, and the risk.
8. **Record the outcome.**
   - The record is an issue titled `[sec-auto record] <item id>` and labeled `sec-auto`.
   - It lists the alerts, the decision, the reason, the PR link and the CI status. The decision is one of fixed, skipped, queued, needs human, or covered by PR #N.
   - An existing record issue is updated rather than duplicated.
   - This step always happens, even when the skill stops early.

### Item ids

The preflight script and the skill must agree on ids, because the script matches
record issue titles exactly.

| Alert type | Item id | Record issue title |
|---|---|---|
| Code scanning | `cs-<alert number>` | `[sec-auto record] cs-4` |
| Secret scanning | `ss-<alert number>` | `[sec-auto record] ss-1` |
| Dependabot package | `dep-<package name lowercased>` | `[sec-auto record] dep-urllib3` |

The preflight script doesn't emit secret-scanning items yet. The `ss-` id is
there for runs of the skill started by hand.

## What humans do

- **Review and merge** `[sec-auto]` PRs. Merging frees a PR slot for the next run.
- **Triage alerts** in GitHub. Agents never dismiss or close them.
- **Read record issues.** "needs human" and "skipped" give a reason. While a record issue is open, the preflight script won't start that item again.
- **Retry an item** by closing its record issue. This changes the item's `version`, so the next run starts it again if it's still open and ranks in the top N.
- **Turn sec-auto off** in either of two ways:
  - Set the repo variable `SEC_AUTO_ENABLED` to anything other than `true`, or delete it. Runs still fire but the preflight starts no sessions.
  - Pause or disable the Automation in Devin. Nothing runs at all.

## Setup

1. **Token.** Create a fine-grained GitHub token. Repository access: only `arunbalaji2019/marlow-lettings`. Repository permissions, all read-only:
   - Variables
   - Pull requests
   - Issues
   - Code scanning alerts
   - Dependabot alerts
   - Metadata (added automatically)
2. **Org secret.** Save the token as the Devin org secret `MARLOW_GH_READ` and attach it to the preflight script. Attaching secrets needs the manage-org-secrets permission.
3. **Repo variable.** Set `SEC_AUTO_ENABLED` to `true` under Settings > Secrets and variables > Actions > Variables.
4. **Automation.**
   - **Triggers:** a GitHub repo webhook pointing at the Automation's webhook URL with its `?secret=`, plus a schedule every weekday at 9:00 PT.
   - **Preflight:** a Python script with the contents of `.agents/automations/preflight.py` and secret `MARLOW_GH_READ`.
   - **Action:** start a session that runs the `remediate-security-alert` skill on this repo for the item it's given.
   - **Network allowlist:** `git-manager.devin.ai`, `api.github.com`, `github.com`, `pypi.org` and `files.pythonhosted.org`.
   - **Run as:** "organization", which is the org's default Automation service user.
   - **GitHub scope:** the Automation's GitHub scope was widened because this repo is public.
   - **Limits:** $6 per session, at most 6 runs per hour, 1 concurrent session with a queue depth of 10.
   - **Notifications:** email on failure.

The preflight token is read-only. Sessions open PRs and issues through Devin's
GitHub integration, not this token.

## Known limitations

- **No re-run while a record is open.** An item with an open record issue doesn't run, even if its package gets a new alert. Close the record to let it run again.
- **Capacity counts every bot PR.** That includes Dependabot and scanner PRs, as `CONTRIBUTING.md` requires, so those can use up all 3 slots.
- **Gaps left in skill step 2.** These came up in review and were deliberately not fixed:
  - An unpatched advisory can go unrecorded when another PR already covers the package's target.
  - A package whose alerts all lack a patched version has no target.
  - A short `[sec-auto]` PR gets its branch raised before triage runs.
