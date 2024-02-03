from flask import Flask, render_template, request, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from textblob import TextBlob
import json
import os
from flask import jsonify

app = Flask(__name__, template_folder='templates')

# Spotify API credentials
SPOTIPY_CLIENT_ID = '55f614b2c700475aac20e12d4a149d33'
SPOTIPY_CLIENT_SECRET = '4dd3a5b009564d25ac8a2464b59f557d'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8888'

USER_DATA_FILE = 'user_data.json'
# Set up Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope='user-library-read user-top-read'))

def analyze_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def save_user_data(username, password):
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump({}, f)
    with open(USER_DATA_FILE, 'r') as f:
        users = json.load(f)

    users[username] = {'password': password}

    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)


def authenticate_user(username, password):
    with open(USER_DATA_FILE, 'r') as f:
        users = json.load(f)

    if username in users and users[username]['password'] == password:
        return True
    else:
        return False


def get_recommendations(sentiment_score, genres):
    if sentiment_score > 0.1:
        genres.extend(['happy', 'remix', 'world', 'indian', 'english'])
    elif sentiment_score < -0.1:
        genres.extend(['sad', 'remix', 'world', 'indian', 'english'])
    else:
        genres.extend(['pop', 'remix', 'world', 'indian', 'english'])

    recommendations = sp.recommendations(seed_genres=genres, limit=5)

    # Include audio features in recommendations
    for track in recommendations['tracks']:
        audio_features = sp.audio_features(track['id'])
        if audio_features:
            track['audio_features'] = {
                'danceability': audio_features[0]['danceability'],
                'energy': audio_features[0]['energy'],
                'tempo': audio_features[0]['tempo']
                # Add more audio features as needed
            }
        else:
            track['audio_features'] = None

    return recommendations




def get_user_top_tracks():
    top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')
    return top_tracks

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    user_input = request.form['user_input']
    sentiment_score = analyze_sentiment(user_input)

    recommended_genres = []
    recommendations = get_recommendations(sentiment_score, recommended_genres)

    user_top_tracks = get_user_top_tracks()

    return render_template('recomendations.html', sentiment_score=sentiment_score, recommendations=recommendations['tracks'], user_top_tracks=user_top_tracks['items'])
# ... (existing code)

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form['search_query']
    search_results = sp.search(q=search_query, type='track', limit=5)

    return render_template('search_results.html', search_results=search_results['tracks']['items'])

# ... (existing code)
# ... (existing code)
@app.route('/ai_recommendation/<track_id>', methods=['GET'])
def ai_recommendation_route(track_id):
    audio_features = sp.audio_features(track_id)

    if audio_features:
        danceability = audio_features[0]['danceability']
        energy = audio_features[0]['energy']

        if danceability > 0.7 and energy > 0.7:
            return "This track is energetic and great for parties!"
        elif danceability < 0.5 and energy < 0.5:
            return "This track has a chill vibe, perfect for relaxing."
        else:
            return "This track has a balanced energy level."
    else:
        return "Audio features not available for the track."


# ... (existing code)
# ... (existing code)



def generate_ai_message(danceability, energy):
    # Customize this function to generate a unique AI message based on audio features
    # Example: Generate a message based on danceability and energy levels
    if danceability > 0.7:
        return "Get ready to hit the dance floor!"
    elif energy < 0.3:
        return "Relax and enjoy the soothing vibes."
    else:
        return "Feel the rhythm and enjoy the music!"


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        save_user_data(username, password)
        return redirect(url_for('index'))

    return render_template('register.html')
# ... (existing code)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate_user(username, password):
            # Redirect to the landing page after successful login
            return redirect(url_for('landing_page'))
            return render_template('login.html', error='Invalid username or password')
            return render_template('login.html')
            # Redirect back to login page if authentication fails
        return redirect(url_for('index'))

@app.route('/landing_page')
def landing_page():
    return render_template('landing_page.html')


@app.route('/react', methods=['POST'])
def react():
    track_id = request.form.get('track_id')
    reaction = request.form.get('reaction')

    # TODO: Implement logic to handle the reaction (update database, store in session, etc.)

    return jsonify({'success': True})




if __name__ == '__main__':
    app.run(debug=True, port=8888)
