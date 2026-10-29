"""Nightly job: push vacancy counts to partner landlords."""
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PARTNER_URL = os.environ.get(
    "PARTNER_URL", "https://partners.example.invalid/vacancies"
)


def make_session():
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[502, 503, 504],
        method_whitelist=["GET", "POST"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def build_payload(listings):
    by_city = {}
    for item in listings:
        by_city[item["city"]] = by_city.get(item["city"], 0) + 1
    return {"vacancies": by_city}


def main():
    from marlow import create_app
    from marlow.db import get_db, to_listing

    app = create_app()
    with app.app_context():
        rows = get_db().execute("SELECT * FROM listings").fetchall()
        payload = build_payload([to_listing(r) for r in rows])
    session = make_session()
    if os.environ.get("DRY_RUN"):
        print(payload)
        return
    session.post(PARTNER_URL, json=payload, timeout=10)


if __name__ == "__main__":
    main()
