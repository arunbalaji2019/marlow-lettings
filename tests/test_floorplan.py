import base64
import os
import pickle


class _MakeDir:
    def __init__(self, path):
        self.path = path

    def __reduce__(self):
        return (os.mkdir, (self.path,))


def _blob(obj, protocol=pickle.HIGHEST_PROTOCOL):
    return base64.b64encode(pickle.dumps(obj, protocol=protocol))


def test_floorplan_counts_rooms(client):
    plan = {"rooms": [{"name": "Kitchen", "area": 12.5}, {"name": "Bed"}]}
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        resp = client.post("/api/floorplan", data=_blob(plan, protocol))
        assert resp.status_code == 200
        assert resp.get_json() == {"rooms": 2}


def test_floorplan_without_rooms(client):
    resp = client.post("/api/floorplan", data=_blob({"name": "Studio"}))
    assert resp.status_code == 200
    assert resp.get_json() == {"rooms": 0}


def test_floorplan_pickle_cannot_run_code(client, tmp_path):
    target = tmp_path / "pwned"
    resp = client.post("/api/floorplan", data=_blob(_MakeDir(str(target))))
    assert not target.exists()
    assert resp.status_code == 400
