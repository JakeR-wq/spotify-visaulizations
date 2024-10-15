from spotipy import Spotify
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
import time

load_dotenv()

# spotify authentication things
SPOTIPY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT")
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIFY_SECRET")
SPOTIPY_REDIRECT_URI = 'http://localhost'
scope = "user-top-read user-read-currently-playing user-read-recently-played"
# token = util.prompt_for_user_token(username='username', scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)
print('Successfully loaded environment variables')

def get_token():
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        print("No valid token found, requesting a new one...")
        token = util.prompt_for_user_token(
            username='username',
            scope=scope,
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI
        )
        return token

    if sp_oauth.is_token_expired(token_info):
        print("Token expired, refreshing...")
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    
    return token_info['access_token']

def collect_songs():
    # Load environment variables
    token = get_token()
    sp = Spotify(auth=token)
    print('Authenticated with Spotify API, ', sp.me()['display_name'])

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

    # Load existing data if the CSV file exists
    csv_file_path = 'currentsong.csv'
    if os.path.exists(csv_file_path):
        existing_df = pd.read_csv(csv_file_path)
        existing_song_ids.update(existing_df['track_id'].tolist())  # Add existing song IDs to the set

    # Check if there is a currently playing song
    if currentsong and currentsong['item'] is not None:
        track = currentsong['item']
        played_at = currentsong['timestamp']  # This is the timestamp when the track is being played

        # Convert milliseconds to a readable date format
        readable_date = datetime.fromtimestamp(played_at / 1000).strftime('%Y-%m-%d %H:%M:%S')

        # Extract relevant track information
        current_song_id = track['id']
        
        # Check if the current song is already playing
        currently_playing_id = existing_df['track_id'].iloc[-1] if not existing_df.empty else None

        artist_id = track['artists'][0]['id']
        artist_info = sp.artist(artist_id)  # Fetch additional artist info using the artist ID
        genres = artist_info['genres']

        if current_song_id != currently_playing_id:
            # Create a new entry for the track
            track_info = {
                'track_name': track['name'],
                'track_id': current_song_id,
                'artist_name': track['artists'][0]['name'],  # Assuming there is at least one artist
                'artist_id': track['artists'][0]['id'],      # Artist ID
                'artist_external_url': track['artists'][0]['external_urls']['spotify'],  # Artist Spotify link
                'album_name': track['album']['name'],
                'album_id': track['album']['id'],
                'album_type': track['album']['album_type'],
                'total_tracks': track['album']['total_tracks'],
                'release_date': track['album']['release_date'],
                'cover_image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'available_markets': ', '.join(track['album']['available_markets']),
                'date_played': readable_date,  # Use the formatted date
                'popularity': track['popularity'],
                'genres': ', '.join(genres),
                'date_listened': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }


            currentsongdf = pd.DataFrame([track_info])

            # Append to CSV file
            currentsongdf.to_csv(csv_file_path, mode='a', header=not pd.io.common.file_exists(csv_file_path), index=False)

            # Print the DataFrame
            print(currentsongdf)
        else:
            print("Song is already playing")

while True:
    collect_songs()
    time.sleep(60)


