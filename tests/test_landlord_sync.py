from marlow.landlord_sync import build_payload


def test_build_payload_counts_by_city():
    listings = [{"city": "London"}, {"city": "London"}, {"city": "Leeds"}]
    assert build_payload(listings) == {"vacancies": {"London": 2, "Leeds": 1}}
