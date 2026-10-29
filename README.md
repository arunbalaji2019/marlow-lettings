# marlow-lettings

Backend for Marlow Lettings: listings, search, landlord sync and PDF/CSV exports.
Serves the public website and the Marlow mobile app.

## Setup

    python3.11 -m venv .venv
    .venv/bin/pip install -r requirements-dev.txt
    .venv/bin/python run.py          # http://localhost:5000

## Tests

    .venv/bin/pytest
    .venv/bin/black --check .

## Jobs

- `python -m marlow.landlord_sync` runs nightly (cron on the app host) and pushes
  vacancy updates to partner landlords.

See CONTRIBUTING.md before opening a PR.
