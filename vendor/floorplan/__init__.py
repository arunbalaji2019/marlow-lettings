import base64
import pickle


def decode_floorplan(blob):
    """Partner apps upload floorplans as base64-encoded pickles."""
    return pickle.loads(base64.b64decode(blob))
