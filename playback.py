
# Standard library imports
import time
import os

# Third party imports
import requests

BASE_URL = 'https://api.spotify.com/v1/'


    Falls back to the first 20 seconds when analysis data is unavailable.
    """
    r = requests.get(BASE_URL + "audio-analysis/" + track_id, headers=auth)
    try:
        data = r.json()
    except ValueError:
        return [0, 20]


def getLoudestSection(track_id, auth):
    """Return the start time and duration of the loudest part of a track.

    Falls back to the first 20 seconds when analysis data is unavailable.
    """
    r = requests.get(BASE_URL + "audio-analysis/" + track_id, headers=auth)
    try:
        data = r.json()
    except ValueError:
        return [0, 20]


    segments = data.get("segments")
    if segments:
        loudest = max(
            segments,
            key=lambda x: x.get("loudness_max", x.get("loudness", 0)),
        )
        return [loudest.get("start", 0), loudest.get("duration", 20)]

    sections = data.get("sections")
    if sections:
        loudest = max(sections, key=lambda x: x.get("loudness", 0))
        return [loudest.get("start", 0), loudest.get("duration", 20)]

    return [0, 20]



def get_available_devices(auth):
    """Return list of available playback devices"""
    r = requests.get(BASE_URL + "me/player/devices", headers=auth)
    return r.json().get("devices", [])



def transfer_playback(device_id, auth):
    """Make sure Spotify is playing on the given device"""
    requests.put(
        BASE_URL + "me/player",
        json={"device_ids": [device_id], "play": False},
        headers=auth,
    )


def playTrack(context_uri, section, pos, auth):
    """Play the loudest section of a track on the user's active device"""
    devices = get_available_devices(auth)
    if not devices:
        return
    device_id = devices[0]["id"]
    transfer_playback(device_id, auth)

    dat = {
        "context_uri": context_uri,
        "offset": {"position": pos},
        "position_ms": int(section[0] * 1000),
    }

    requests.put(
        "https://api.spotify.com/v1/me/player/play",
        params={"device_id": device_id},
        json=dat,
        headers=auth,
    )
    time.sleep(min(section[1], 25))
    requests.put(
        "https://api.spotify.com/v1/me/player/pause",
        params={"device_id": device_id},
        headers=auth,
    )



def getTrackIds(playlistId, auth):
    r = requests.get('https://api.spotify.com/v1/playlists/{}'.format(playlistId), headers=auth)
    if r.status_code != 200:
        return []
    try:
        r = r.json()
    except ValueError:
        return []
    trackIds = []
    for t in r['tracks']['items']:
        trackIds.append(t['track']['id'])
    return trackIds


def getTracks(playlistId, auth):
    r = requests.get('https://api.spotify.com/v1/playlists/{}'.format(playlistId), headers=auth)
    if r.status_code != 200:
        return []
    try:
        r = r.json()
    except ValueError:
        return []
    tracks = []
    for t in r['tracks']['items']:
        tracks.append(t['track'])

    return tracks


def playTracks(trackIds, playlistId, auth):
    for i in range(len(trackIds)):
        s = getLoudestSection(trackIds[i], auth)
        #r = requests.post('https://adaptatune.herokuapp.com/')
        playTrack('spotify:playlist:{}'.format(playlistId), s, i, auth)

    
def nextTrack(auth):
    r = requests.post('https://api.spotify.com/v1/me/player/next', headers=auth)


def playSingleTrack(playlistId, trackId, auth, pos):
    """Play a single track starting at its loudest section."""
    s = getLoudestSection(trackId, auth)
    try:
        idx = int(pos)
    except (TypeError, ValueError):
        idx = 0
    playTrack('spotify:playlist:{}'.format(playlistId), s, idx, auth)


def get_audio_features(track_ids, auth):
    """Return audio features for a list of track ids"""
    if not track_ids:
        return []
    params = {"ids": ",".join(track_ids)}
    r = requests.get(BASE_URL + "audio-features", params=params, headers=auth)
    if r.status_code != 200:
        return []
    try:
        return r.json().get("audio_features", [])
    except ValueError:
        return []


def categorize_user(features):
    """Simple categorization based on average energy/valence/danceability."""
    if not features:
        return "Unknown"
    energy = sum(f["energy"] for f in features if f) / len(features)
    valence = sum(f["valence"] for f in features if f) / len(features)
    dance = sum(f["danceability"] for f in features if f) / len(features)
    if energy > 0.7 and valence > 0.6:
        return "Upbeat"
    if energy < 0.4 and valence < 0.4:
        return "Chill"
    if dance > 0.7:
        return "Dance"
    return "Balanced"


def get_recommendations(seed_tracks, auth, limit=20):
    """Return Spotify recommendations for the given seed tracks.

    Any of the seed tracks may appear in the response, so filter them out
    before returning the recommended tracks.
    """
    if not seed_tracks:
        return []

    params = {"seed_tracks": ",".join(seed_tracks[:5]), "limit": limit}

    # Use average audio features to steer recommendations towards the user's vibe
    feat = get_audio_features(seed_tracks[:5], auth)
    if feat:
        avg_energy = sum(f["energy"] for f in feat if f) / len(feat)
        avg_valence = sum(f["valence"] for f in feat if f) / len(feat)
        params.update({"target_energy": avg_energy, "target_valence": avg_valence})

    r = requests.get(BASE_URL + "recommendations", params=params, headers=auth)
    if r.status_code != 200:
        return []
    try:
        data = r.json()
    except ValueError:
        return []

    tracks = data.get("tracks", [])
    seed_set = set(seed_tracks)
    filtered = [t for t in tracks if t.get("id") not in seed_set]
    return filtered


def get_user_profile(auth):
    r = requests.get(BASE_URL + "me", headers=auth)
    try:
        return r.json()
    except ValueError:
        return {}



def create_playlist(user_id, name, auth):
    """Create a playlist and return its id or None on failure."""

    payload = {"name": name, "description": "Generated by Adaptune AI"}
    r = requests.post(
        BASE_URL + f"users/{user_id}/playlists", json=payload, headers=auth
    )
    if r.status_code not in (200, 201):
        return None
    try:
        return r.json().get("id")
    except ValueError:
        return None


def add_tracks_to_playlist(playlist_id, track_uris, auth):
    """Add tracks to a playlist, returning True on success."""
    if not playlist_id or not track_uris:
        return False
    r = requests.post(
        BASE_URL + f"playlists/{playlist_id}/tracks",
        json={"uris": track_uris},
        headers=auth,
    )
    return r.status_code in (200, 201)


def create_playlist_with_tracks(user_id, name, track_uris, auth):
    playlist_id = create_playlist(user_id, name, auth)
    if not playlist_id:
        return None
    # small delay to ensure playlist is fully created on Spotify
    time.sleep(0.5)
    if not add_tracks_to_playlist(playlist_id, track_uris, auth):
        return None

    return playlist_id


if __name__ == "__main__":
    playTracks()


