def test_search_matches_part_of_title(client):
    data = client.get("/api/search?q=Clapham").get_json()
    assert [d["id"] for d in data] == [1, 5]


def test_search_empty_query_returns_all(client):
    assert len(client.get("/api/search").get_json()) == 5


def test_search_no_match(client):
    assert client.get("/api/search?q=Glasgow").get_json() == []
