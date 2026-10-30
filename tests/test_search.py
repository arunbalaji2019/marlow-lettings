def test_search_matches_part_of_title(client):
    data = client.get("/api/search?q=Clapham").get_json()
    assert [d["id"] for d in data] == [1, 5]


def test_search_empty_query_returns_all(client):
    assert len(client.get("/api/search").get_json()) == 5


def test_search_no_match(client):
    assert client.get("/api/search?q=Glasgow").get_json() == []


def test_search_quote_in_query_is_not_sql(client):
    resp = client.get("/api/search", query_string={"q": "x' OR 1=1 --"})
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_search_union_injection_returns_nothing(client):
    q = "x' UNION SELECT 1,2,3,4,5 --"
    assert client.get("/api/search", query_string={"q": q}).get_json() == []
