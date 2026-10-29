import os


def test_export_existing_file(client):
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    resp = client.get("/export/listings-2026-10.csv")
    assert resp.status_code == 200
    assert b"Clapham" in resp.data
