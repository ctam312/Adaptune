
# used to access environment variables securely (sensitive data)
from email.quoprimime import body_check
import os

# used to encode strings into bytes and back
import base64

# used to convert JSON data into strings
import json
import requests
import time


# TODO: get auth token from client
token_request_url = "https://accounts.spotify.com/api/token"

CLIENT_ID = 'e7dd4d704dbf462da4d1bb541f55695f'
CLIENT_SECRET = '07bc8202e8404f7e82df0d49a7128129'

# encode credentials into bytes, then decode into a string for the HTTP POST request to Spotify to authenticate
BASE64_ENCODED_HEADER_STRING = base64.b64encode(bytes(f"{CLIENT_ID}:{CLIENT_SECRET}", "ISO-8859-1")).decode("ascii")

#initializing dictionaries for HTTP POST request
headers = {}
data = {}

headers['Authorization'] = f"Basic {BASE64_ENCODED_HEADER_STRING}"

data['grant_type'] = "client_credentials"
data['json'] = True
data['scope'] = ['user-read-recently-played', 'user-modify-playback-state', 'user-read-playback-position', 'app-remote-control', 'user-read-playback-state', 'playlist-read-private']

r = requests.post(url=token_request_url, headers=headers, data=data)
  
token = r.json().get('access_token')


headers = {
    'Authorization': 'Bearer {token}'.format(token=token)
}


BASE_URL = 'https://api.spotify.com/v1/'



def getLoudestSection(track_id, auth):
    """Return the start time and duration of the loudest section for a track.

    If Spotify's analysis data is unavailable, fall back to the first 20
    seconds of the track so playback still works instead of throwing a
    KeyError.
    """
    r = requests.get(BASE_URL + 'audio-analysis/' + track_id, headers=auth)
    data = r.json()

    segments = data.get('sections') or data.get('segments')
    if not segments:
        return [0, 20]

    loudest = max(segments, key=lambda x: x.get('loudness', 0))
    return [loudest.get('start', 0), loudest.get('duration', 20)]



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
        data=json.dumps(dat),
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
    r = r.json()
    trackIds = []
    for t in r['tracks']['items']:
        trackIds.append(t['track']['id'])
    return trackIds


def getTracks(playlistId, auth):
    r = requests.get('https://api.spotify.com/v1/playlists/{}'.format(playlistId), headers=auth)
    r = r.json()
    tracks = []
    for t in r['tracks']['items']:
        tracks.append(t['track'])

    return tracks


def playTracks(trackIds, playlistId, auth):
    for i in range(len(trackIds)):
        s = getLoudestSection(trackIds[i], auth)
        print(s)
        #r = requests.post('https://adaptatune.herokuapp.com/')
        playTrack('spotify:playlist:{}'.format(playlistId), s, i, auth)

    
def nextTrack(auth):
    r = requests.post('https://api.spotify.com/v1/me/player/next', headers=auth)


def playSingleTrack(playlistId, trackId, auth, pos):
    s = getLoudestSection(trackId, auth)
    playTrack('spotify:playlist:{}'.format(playlistId), s, pos, auth)


def get_audio_features(track_ids, auth):
    """Return audio features for a list of track ids"""
    if not track_ids:
        return []
    params = {"ids": ",".join(track_ids)}
    r = requests.get(BASE_URL + "audio-features", params=params, headers=auth)
    return r.json().get("audio_features", [])


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
    params = {"seed_tracks": ",".join(seed_tracks[:5]), "limit": limit}
    r = requests.get(BASE_URL + "recommendations", params=params, headers=auth)
    return r.json().get("tracks", [])


def get_user_profile(auth):
    r = requests.get(BASE_URL + "me", headers=auth)
    return r.json()


def create_playlist_with_tracks(user_id, name, track_uris, auth):
    payload = {"name": name, "description": "Generated by Adaptune AI"}
    r = requests.post(BASE_URL + f"users/{user_id}/playlists", json=payload, headers=auth)
    playlist_id = r.json().get("id")
    if playlist_id:
        requests.post(BASE_URL + f"playlists/{playlist_id}/tracks", json={"uris": track_uris}, headers=auth)
    return playlist_id


if __name__ == "__main__":
    playTracks()


