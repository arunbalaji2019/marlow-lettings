"""Preflight check for the marlow-lettings sec-auto Automation.

Emits one item per open code-scanning alert and one per Dependabot package,
up to the free [sec-auto] PR slots, skipping any item that already has an open
"[sec-auto record] <id>" issue. An item's version is its sorted alert numbers
plus ":<number of closed record issues for that id>". Local test mode: `python preflight.py --test`
prints the items instead of writing $OUTPUT_FILE (still needs MARLOW_GH_READ).
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

REPO = "arunbalaji2019/marlow-lettings"
API = "https://api.github.com"
MAX_BOT_PRS = 3
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
# Code-scanning rules without a security severity only have error/warning/note.
RULE_SEVERITY = {"error": "high", "warning": "medium", "note": "low"}
RECORD_TITLE = re.compile(r"^\[sec-auto record\] (\S+)")
DEADLINE = time.monotonic() + 50
TOKEN = os.environ.get("MARLOW_GH_READ", "")


def request(url):
    if time.monotonic() > DEADLINE:
        raise TimeoutError("time budget used up")
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp), resp.headers.get("Link", "")


def get_all(path):
    url = f"{API}/repos/{REPO}/{path}"
    results = []
    while url:
        page, link = request(url)
        results.extend(page)
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = match.group(1) if match else None
    return results


def enabled():
    try:
        var, _ = request(f"{API}/repos/{REPO}/actions/variables/SEC_AUTO_ENABLED")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
        raise
    return var.get("value", "").strip().lower() == "true"


def free_slots():
    prs = get_all("pulls?state=open&per_page=100")
    busy = sum(
        1
        for pr in prs
        if pr["user"]["type"] == "Bot" or pr["title"].startswith("[sec-auto]")
    )
    return max(0, MAX_BOT_PRS - busy)


def code_scanning_items():
    items = []
    for alert in get_all("code-scanning/alerts?state=open&per_page=100"):
        rule = alert["rule"]
        severity = rule.get("security_severity_level") or RULE_SEVERITY.get(
            rule.get("severity"), "low"
        )
        number = alert["number"]
        items.append(
            {
                "id": f"cs-{number}",
                "version": str(number),
                "kind": "code-scanning",
                "alert_number": number,
                "severity": severity,
                "rule": rule["id"],
                "url": alert["html_url"],
            }
        )
    return items


def dependabot_items():
    packages = {}
    for alert in get_all("dependabot/alerts?state=open&per_page=100"):
        name = alert["dependency"]["package"]["name"].lower()
        severity = alert["security_advisory"]["severity"]
        pkg = packages.setdefault(name, {"numbers": [], "severity": "low"})
        pkg["numbers"].append(alert["number"])
        if SEVERITY_RANK[severity] < SEVERITY_RANK[pkg["severity"]]:
            pkg["severity"] = severity
    items = []
    for name, pkg in packages.items():
        numbers = sorted(pkg["numbers"])
        items.append(
            {
                "id": f"dep-{name}",
                "version": ",".join(map(str, numbers)),
                "kind": "dependabot",
                "package": name,
                "alert_numbers": numbers,
                "severity": pkg["severity"],
            }
        )
    return items


def record_issues():
    """Return (ids with an open record issue, closed record count per id)."""
    open_ids, closed = set(), {}
    for issue in get_all("issues?state=all&per_page=100"):
        match = RECORD_TITLE.match(issue["title"])
        if not match or "pull_request" in issue:
            continue
        item_id = match.group(1)
        if issue["state"] == "open":
            open_ids.add(item_id)
        else:
            closed[item_id] = closed.get(item_id, 0) + 1
    return open_ids, closed


def build_items():
    if not enabled():
        return []
    slots = free_slots()
    if slots == 0:
        return []
    open_ids, closed = record_issues()
    items = []
    for item in code_scanning_items() + dependabot_items():
        if item["id"] in open_ids:
            continue
        # Closing a record bumps the version, so the item fires again.
        item["version"] += f":{closed.get(item['id'], 0)}"
        items.append(item)
    items.sort(key=lambda item: (SEVERITY_RANK[item["severity"]], item["id"]))
    return items[:slots]


def main():
    if not TOKEN:
        sys.exit("MARLOW_GH_READ is not set")
    output = {"items": build_items()}
    if "--test" in sys.argv:
        print(json.dumps(output, indent=2))
        return
    with open(os.environ["OUTPUT_FILE"], "w") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
