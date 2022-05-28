# used to access environment variables securely (sensitive data)
from email.quoprimime import body_check
import os

# used to encode strings into bytes and back
import base64

# used to convert JSON data into strings
import json
import requests
from sklearn.metrics import r2_score
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
  
token = r.json()['access_token']
print(token)

headers = {
    'Authorization': 'Bearer {token}'.format(token=token)
}


BASE_URL = 'https://api.spotify.com/v1/'



def getLoudestSection(track_id):

    r = requests.get(BASE_URL + 'audio-analysis/' + track_id, headers=headers)

    r = r.json()

    #print(json.dumps(r['segments'], indent=2))

    segments = r['sections']

    loudest_section = max(segments, key = lambda x: x['loudness'])

    return [loudest_section['start'], loudest_section['duration']]


playback_token = 'BQD-nTzrs747sVsoYRLqAKxx_gxV1jegjEhhsO3DI9vlfyPu0uNprMXKNDWWzlC7brt3ZYEt4kBsFpr6c5wYbx1w6W21lIhzu2Sp5R0wZgW3sxl9kdRJdPpAWcFjFiCtxjWA056a23cqJLHr5H1HQl2WjcwL0ZHUoiUD5qZLC_9V4EFA23fIOayGbrnBMz8joWbRiKKB9XpkbQsKYphyFLGUhEdnrbTAFG2wjSXN-rMkPEsq6DeniW991aPyuOC2CIJIr-njIw'

headers_playback = {
        'Authorization': 'Bearer {token}'.format(token=playback_token),
    }

def playTrack(context_uri, section, pos):

    dat= {
    "context_uri": context_uri,
    "offset": {'position': pos},
    "position_ms": int(section[0]*1000)
    }

    r = requests.put('https://api.spotify.com/v1/me/player/play', data=json.dumps(dat), headers=headers_playback)
    time.sleep(section[1])
    r = requests.put('https://api.spotify.com/v1/me/player/pause', headers=headers_playback)



def getTrackIds(playlistId):
    r = requests.get('https://api.spotify.com/v1/playlists/{}'.format(playlistId), headers=headers)
    r = r.json()
    trackIds = []
    for t in r['tracks']['items']:
        trackIds.append(t['track']['id'])
    return trackIds


def getTrackNames(playlistId):
    r = requests.get('https://api.spotify.com/v1/playlists/{}'.format(playlistId), headers=headers)
    r = r.json()
    trackIds = []
    for t in r['tracks']['items']:
        trackIds.append(t['track']['name'])
    return trackIds

tracksIds = getTrackIds('37i9dQZEVXcVidpgiUusHN')
tracksNames = getTrackNames('37i9dQZEVXcVidpgiUusHN')

for i in range(len(tracksIds)):
    s = getLoudestSection(tracksIds[i])
    print("Playing {}  |  start: {}; duration: {}".format(tracksNames[i], s[0], s[1]))
    playTrack('spotify:playlist:37i9dQZEVXcVidpgiUusHN', s, i) 
    r = requests.post('https://api.spotify.com/v1/me/player/next', headers=headers_playback)
