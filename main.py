from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

# spotify authentication things
SPOTIPY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT")
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIFY_SECRET")
SPOTIPY_REDIRECT_URI = 'http://localhost'
print('Successfully loaded environment variables')
scope = "user-top-read user-read-currently-playing user-read-recently-played"
# token = util.prompt_for_user_token(username='username', scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)

# have to create this and add an empty json object, in this case just put "{}" in there to not break json library
# this could be fixed just no point 
TOKEN_FILE = '.cache'

# put the new token into the .cache file
def save_token(token_info):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_info, f)

# loads a token from .cache
def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        token_info = json.load(f)
    return token_info

# get our token, check if it's valid, check if it needs refreshing, return our token
def get_token():
    token_info = load_token()

    if not token_info:
        print("No valid token found, requesting a new one...")
        token_info = sp_oauth.get_access_token(code=None)
        save_token(token_info)
        return token_info['access_token']

    if sp_oauth.is_token_expired(token_info):
        print("Token expired, refreshing...")
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        save_token(token_info)
    token_time = datetime.fromtimestamp(token_info['expires_at']) - datetime.now()
    print("token is valid, continuing...")
    print("Token life remaining: ", token_time)
    return token_info['access_token']

def welcome():
    token = get_token()
    sp = Spotify(auth=token)
    print('Authenticated with Spotify API, ', sp.me()['display_name'])

def collect_songs():
    # Load environment variables
    token = get_token()
    sp = Spotify(auth=token)

    # leaving this here, may possibly use this

    # tracks = []
    # spotifyreturn = sp.current_user_recently_played(limit=50)
    # for item in spotifyreturn['items']:
    #     track = item['track']
    #     tracks.append({
    #         'name': track['name'],
    #         'artist': track['artists'][0]['name'],
    #         'album': track['album']['name'],
    #         'date': item['played_at'],
    #         'popularity': track['popularity']
    #     })
    # df = pd.DataFrame(tracks)
    # csv_file_path = 'spotifydata.csv'
    # df.to_csv(csv_file_path, mode='a', header=not pd.io.common.file_exists(csv_file_path), index=False)
    # print(df)

    currentsong = sp.currently_playing()

    existing_song_ids = set()
    existing_df = pd.DataFrame()

    # this will be usefull when checking for duplicates
    csv_file_path = 'currentsong.csv'
    if os.path.exists(csv_file_path):
        existing_df = pd.read_csv(csv_file_path)
        existing_song_ids.update(existing_df['track_id'].tolist())

    # Check if there is a currently playing song
    if currentsong and currentsong['item'] is not None:
        track = currentsong['item']
        played_at = currentsong['timestamp']

        # date is returned in milliseconds, turn into a readable date
        readable_date = datetime.fromtimestamp(played_at / 1000).strftime('%Y-%m-%d %H:%M:%S')

        # get the current track id
        current_song_id = track['id']
        
        # looking at row above to see if this song has already been played
        currently_playing_id = existing_df['track_id'].iloc[-1] if not existing_df.empty else None

        # get the genres of the artist
        artist_id = track['artists'][0]['id']
        artist_info = sp.artist(artist_id)  
        genres = artist_info['genres']

        # get some cool track info 
        # https://developer.spotify.com/documentation/web-api/reference/get-audio-features
        track_data = sp.audio_features(current_song_id)

        # making sure we dont add duplicates; listening to the same song
        if current_song_id != currently_playing_id:
            # Create a new entry for the track
            track_info = {
                'track_name': track['name'],
                'track_id': current_song_id,
                'artist_name': track['artists'][0]['name'],  
                'artist_id': track['artists'][0]['id'],      
                'artist_external_url': track['artists'][0]['external_urls']['spotify'],  
                'album_name': track['album']['name'],
                'album_id': track['album']['id'],
                'album_type': track['album']['album_type'],
                'total_tracks': track['album']['total_tracks'],
                'release_date': track['album']['release_date'],
                'cover_image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'date_played': readable_date,
                'popularity': track['popularity'],
                'genres': ', '.join(genres),
                'acousticness': track_data[0]['acousticness'],
                'danceability': track_data[0]['danceability'],
                'duration_ms': track_data[0]['duration_ms'],
                'energy': track_data[0]['energy'],
                'instrumentalness': track_data[0]['instrumentalness'],
                'key': track_data[0]['key'],
                'liveness': track_data[0]['liveness'],
                'loudness': track_data[0]['loudness'],
                'mode': track_data[0]['mode'],
                'speechiness': track_data[0]['speechiness'],
                'tempo': track_data[0]['tempo'],
                'time_signature': track_data[0]['time_signature'],
                'valence': track_data[0]['valence']

            }

            # put the track's info into a dataframe then append to the csv
            currentsongdf = pd.DataFrame([track_info])
            currentsongdf.to_csv(csv_file_path, mode='a', header=not pd.io.common.file_exists(csv_file_path), index=False)

            # want to see what is being added
            print(currentsongdf)
        else:
            print("Song is already playing")
welcome()
while True:
    collect_songs()
    time.sleep(60)


