import requests

DISTRUSTED_ROOTS = [
    "TrustCor",  # GHSA-43fp-rhv2-5gv8
    "e-Tugra",  # GHSA-xqr8-7jwr-rhp7
    "emSign",  # GHSA-6q48-6c7w-9gw2
]


def test_ca_bundle_excludes_distrusted_roots():
    with open(requests.certs.where(), encoding="utf-8") as f:
        bundle = f.read()
    for root in DISTRUSTED_ROOTS:
        assert root not in bundle, f"{root} root CA still in requests' CA bundle"
