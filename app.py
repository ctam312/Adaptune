from flask import *
from authorization import SpotifyClient
from urllib.parse import urlparse
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
    client_id = 'e7dd4d704dbf462da4d1bb541f55695f'
    client_secret = '07bc8202e8404f7e82df0d49a7128129'
    spotify_client = SpotifyClient(client_id, client_secret, port=5000)
    auth_url = spotify_client.get_auth_url()
    print('hello')
    return redirect(auth_url)
    

@app.route("/callback/q")
def callback():
    auth_token = request.args['code']
    client_id = 'e7dd4d704dbf462da4d1bb541f55695f'
    client_secret = '07bc8202e8404f7e82df0d49a7128129'
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
            print(id)
            tracks = getTracks(id, session["auth"])
            session["playlistId"] = id
            print(tracks)
        except:
            return "invalid playlist link"

        return render_template('user_playlist.html', tracks=tracks, playlistId=id, currentTrack = None, len=len(tracks)) 


@app.route('/background_process_test')
def background_process_test():
    args = request.args.to_dict()

    tracks = getTracks(session["playlistId"], session["auth"])
    playSingleTrack(session["playlistId"], args['trackId'], session["auth"], args['index'])
    return render_template('user_playlist.html', tracks=tracks, playlistId=session["playlistId"], len=len(tracks))


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
    uris = [t['uri'] for t in recs]
    user = get_user_profile(auth)
    playlist_id = create_playlist_with_tracks(user['id'], 'Adaptune Recommendations', uris, auth)
    return render_template('recommendations.html', playlist_id=playlist_id, category=category)

