def test_list_listings(client):
    resp = client.get("/api/listings")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 5
    for item in data:
        assert set(item) == {"id", "title", "city", "rent", "bedrooms"}


def test_get_listing(client):
    resp = client.get("/api/listings/2")
    assert resp.status_code == 200
    assert resp.get_json()["city"] == "Edinburgh"


def test_missing_listing(client):
    assert client.get("/api/listings/999").status_code == 404
