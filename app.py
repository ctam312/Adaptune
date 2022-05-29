from flask import *
from authorization import SpotifyClient
from urllib.parse import urlparse
from playback import getTrackIds, playSingleTrack, playTracks, playTrack
import subprocess


app = Flask(__name__)
app.secret_key = 'test'
@app.route('/')
def home():
    return render_template('home.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    client_id = 'e7dd4d704dbf462da4d1bb541f55695f'
    client_secret = '07bc8202e8404f7e82df0d49a7128129'
    spotify_client = SpotifyClient(client_id, client_secret)
    auth_url = spotify_client.get_auth_url()
    print('hello')
    return redirect(auth_url)
    

@app.route("/callback/q")
def callback():
    auth_token = request.args['code']
    client_id = 'e7dd4d704dbf462da4d1bb541f55695f'
    client_secret = '07bc8202e8404f7e82df0d49a7128129'
    spotify_client = SpotifyClient(client_id, client_secret)
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
            tracks = getTrackIds(id, session["auth"])
            # use spotify api to check if valid playlistId
            session["tracks"] = tracks
            session["playlistId"] = id
        except:
            return "invalid playlist link"

        return render_template('user_playlist.html', tracks=tracks, playlistId=id, currentTrack = None, len=len(tracks)) 


@app.route('/background_process_test')
def background_process_test():
    args = request.args.to_dict()
    print(args)
    playSingleTrack(session["playlistId"], args['trackId'], session["auth"], args['index'])
    return render_template('user_playlist.html', tracks=session["tracks"], playlistId=session["playlistId"], len=len(session["tracks"]))