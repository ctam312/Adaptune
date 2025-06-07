import sys
import os
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# provide a minimal 'requests' stub if the real package is unavailable
if 'requests' not in sys.modules:
    requests_stub = types.ModuleType('requests')

    class DummyResp:
        def __init__(self, data=None):
            self._data = data or {}
            self.status_code = 200
        def json(self):
            return self._data

    def _post(*args, **kwargs):
        return DummyResp({"access_token": "token"})

    def _get(*args, **kwargs):
        return DummyResp()

    def _put(*args, **kwargs):
        return DummyResp()

    requests_stub.get = _get
    requests_stub.post = _post
    requests_stub.put = _put

    sys.modules['requests'] = requests_stub

import playback

class MockResponse:
    def __init__(self, data, raise_json=False):
        self.data = data
        self.raise_json = raise_json

    def json(self):
        if self.raise_json:
            raise ValueError("bad json")
        return self.data

def test_get_loudest_section_segments(monkeypatch):
    def mock_get(url, headers=None):
        return MockResponse({"segments": [
            {"start": 0, "duration": 10, "loudness_max": -6},
            {"start": 15, "duration": 5, "loudness_max": -1}
        ]})
    monkeypatch.setattr(playback.requests, "get", mock_get)
    result = playback.getLoudestSection("abc", {})
    assert result == [15, 5]

def test_get_loudest_section_sections(monkeypatch):
    def mock_get(url, headers=None):
        return MockResponse({"sections": [
            {"start": 0, "duration": 10, "loudness": -6},
            {"start": 20, "duration": 8, "loudness": -2}
        ]})
    monkeypatch.setattr(playback.requests, "get", mock_get)
    result = playback.getLoudestSection("abc", {})
    assert result == [20, 8]

def test_get_loudest_section_fallback(monkeypatch):
    def mock_get(url, headers=None):
        return MockResponse({}, raise_json=True)
    monkeypatch.setattr(playback.requests, "get", mock_get)
    result = playback.getLoudestSection("abc", {})
    assert result == [0, 20]

def test_categorize_user():
    upbeat = [{"energy":0.8,"valence":0.7,"danceability":0.5}]
    assert playback.categorize_user(upbeat) == "Upbeat"
    chill = [{"energy":0.3,"valence":0.3,"danceability":0.5}]
    assert playback.categorize_user(chill) == "Chill"
    dance = [{"energy":0.5,"valence":0.5,"danceability":0.8}]
    assert playback.categorize_user(dance) == "Dance"
    balanced = [{"energy":0.5,"valence":0.5,"danceability":0.5}]
    assert playback.categorize_user(balanced) == "Balanced"

def test_get_recommendations_filters_seed(monkeypatch):
    def mock_get(url, params=None, headers=None):
        return MockResponse({"tracks": [
            {"id": "id1"}, {"id": "id3"}, {"id": "id2"}, {"id": "id4"}
        ]})
    monkeypatch.setattr(playback.requests, "get", mock_get)
    recs = playback.get_recommendations(["id1","id2"], {})
    assert [t["id"] for t in recs] == ["id3", "id4"]

def test_get_recommendations_bad_json(monkeypatch):
    def mock_get(url, params=None, headers=None):
        return MockResponse({}, raise_json=True)
    monkeypatch.setattr(playback.requests, "get", mock_get)
    recs = playback.get_recommendations(["id1"], {})
    assert recs == []
