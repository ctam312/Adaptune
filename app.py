from flask import *
from authorization import SpotifyClient
from urllib.parse import urlparse
import threading
import os
from playback import (
    getTrackIds,
    playSingleTrack,
    playTracks,
    playTrack,
    getTracks,
    get_audio_features,
    categorize_user,
    get_recommendations,
    create_playlist_with_tracks,
    get_user_profile,
)


app = Flask(__name__)
app.secret_key = 'test'
@app.route('/')
def home():
    return render_template('home.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    if not client_id or not client_secret:
        return (
            "Spotify credentials not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
            500,
        )
    spotify_client = SpotifyClient(client_id, client_secret, port=5000)
    auth_url = spotify_client.get_auth_url()
    return redirect(auth_url)
    

@app.route("/callback/q")
def callback():
    auth_token = request.args['code']
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    spotify_client = SpotifyClient(client_id, client_secret, port=5000)
    spotify_client.get_authorization(auth_token)
    authorization_header = spotify_client.authorization_header
    session["auth"] = authorization_header
    return redirect(url_for("playlist"))

@app.route("/playlist", methods=['GET', 'POST'])
def playlist():
    if request.method == 'GET':
        return render_template('playlist.html')
    else:
        
        data = request.form['link']
        try:
            # get playlistId from link
            o = urlparse(data)
            p = o.path.split('/')
            id = p[-1]
            tracks = getTracks(id, session["auth"])
            session["playlistId"] = id
        except:
            return "invalid playlist link"

        return render_template('user_playlist.html', tracks=tracks, playlistId=id, currentTrack = None, len=len(tracks)) 


@app.route('/background_process_test')
def background_process_test():
    args = request.args.to_dict()
    thread = threading.Thread(
        target=playSingleTrack,
        args=(
            session["playlistId"],
            args["trackId"],
            session["auth"],
            args["index"],
        ),
    )
    thread.start()
    return ("", 204)


@app.route('/like_track', methods=['POST'])
def like_track():
    track_id = request.form.get('track_id')
    liked = session.get('liked_tracks', [])
    if track_id in liked:
        liked.remove(track_id)
    else:
        liked.append(track_id)
    session['liked_tracks'] = liked
    return ('', 204)


@app.route('/generate_playlist')
def generate_playlist():
    liked = session.get('liked_tracks', [])
    if not liked:
        return 'No tracks liked', 400
    auth = session['auth']
    features = get_audio_features(liked, auth)
    category = categorize_user(features)
    recs = get_recommendations(liked[:5], auth)
    # Remove any songs that the user already liked to keep the playlist fresh
    recs = [t for t in recs if t.get('id') not in liked]
    liked_uris = [f"spotify:track:{tid}" for tid in liked]
    rec_uris = [t['uri'] for t in recs]
    uris = liked_uris + rec_uris
    user = get_user_profile(auth)
    user_id = user.get('id')
    if not user_id:
        return 'Failed to fetch user profile', 500
    playlist_name = category
    playlist_id = create_playlist_with_tracks(user_id, playlist_name, uris, auth)
    if not playlist_id:
        return 'Failed to create playlist', 500
    return render_template(
        'recommendations.html',
        playlist_id=playlist_id,
        category=category,
        recs=recs,
        playlist_name=playlist_name,
    )

