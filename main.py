from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, session
import os
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

MUSIC_FOLDER = "static/music"
USERS_DATA_FILE = "users_data.json"

USERNAME = "admin"
PASSWORD = "1234"

SONG_METADATA = {
    0: {"artist": "Tory Lanez", "genre": "Hip-Hop", "length": 200},
    1: {"artist": "Placeholder", "genre": "Classical", "length": 355},
    2: {"artist": "Tory Lanez", "genre": "Hip-Hop", "length": 326},
}

def load_users():
    if os.path.exists(USERS_DATA_FILE):
        with open(USERS_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_tracks():
    #Loops through all mp3 files in the music folder and extracts key info
    mp3_files = sorted([f for f in os.listdir(MUSIC_FOLDER) if f.endswith(".mp3")])
    return [{"id": i, "name": f[:-4], "file": f} for i, f in enumerate(mp3_files)]

def build_song_library():

    #Creates a library of songs, including the genre and artist name
    mp3_files = sorted([f for f in os.listdir(MUSIC_FOLDER) if f.endswith(".mp3")])

    library = []

    for i, f in enumerate(mp3_files):
        metadata = SONG_METADATA.get(i, {
            "artist": "Unknown Artist",
            "genre": "Unknown Genre",
            "length": 0
        })

        library.append({
            "id": i,
            "title": f[:-4],
            "artist": metadata["artist"],
            "genre": metadata["genre"],
            "length": metadata["length"]
        })

    return library

SONG_LIBRARY = build_song_library()


@app.route("/")
def login_page():
    if session.get("logged_in"):
        return redirect("/home")
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if username == USERNAME and password == PASSWORD:
        session["logged_in"] = True
        session["current_user"] = username
        return redirect("/home")
    return render_template("login.html", error="Invalid credentials")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/home")
def home():
    if not session.get("logged_in"):
        return redirect("/")
    users = load_users()
    current_user = session.get("current_user", "admin")
    user_data = users.get(current_user, {})
    return render_template(
        "index.html",
        tracks=load_tracks(),
        user_data=user_data,
        song_library=SONG_LIBRARY
    )

#Plays a track
@app.route("/track/<int:track_id>")
def get_track(track_id):
    if not session.get("logged_in"):
        return "Unauthorized", 401
    tracks = load_tracks()
    if track_id < 0 or track_id >= len(tracks):
        return "Track not found", 404
    return send_from_directory(MUSIC_FOLDER, tracks[track_id]["file"], mimetype="audio/mp3")

#Returns just the tracks as a json
@app.route("/tracks")
def get_tracks():
    if not session.get("logged_in"):
        return jsonify([])
    return jsonify(load_tracks())

#Returns the song library as a json
@app.route("/api/song-library")
def get_song_library():
    if not session.get("logged_in"):
        return jsonify([])
    return jsonify(SONG_LIBRARY)


@app.route("/api/user/profile", methods=["GET"])
def get_user_profile():
    if not session.get("logged_in"):
        return jsonify({"error": "Not logged in"}), 401
    users = load_users()
    return jsonify(users.get(session.get("current_user"), {}))

#Creates a user profile and saves it to the session storage
@app.route("/api/user/create", methods=["POST"])
def create_user_profile():
    if not session.get("logged_in"):
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    current_user = session.get("current_user")
    users = load_users()
    users[current_user] = {
        "name": data.get("name", "").strip(),
        "dob":  data.get("dob", ""),
        "favourite_artist": data.get("favourite_artist", "").strip(),
        "favourite_genre":  data.get("favourite_genre",  "").strip(),
    }
    save_users(users)
    return jsonify({"success": True})

#Populates the user data with a json including the fav genre and artist
@app.route("/api/user/update", methods=["POST"])
def update_user_profile():
    if not session.get("logged_in"):
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    current_user = session.get("current_user")
    users = load_users()
    if current_user not in users:
        return jsonify({"error": "Profile not found — create one first"}), 404
    users[current_user]["favourite_artist"] = data.get("favourite_artist", "").strip()
    users[current_user]["favourite_genre"]  = data.get("favourite_genre",  "").strip()
    save_users(users)
    return jsonify({"success": True})


#Loops through song library and adds songs until time limit reached
@app.route("/api/playlist/generate-by-time", methods=["POST"])
def generate_playlist_by_time():
    if not session.get("logged_in"):
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    try:
        time_limit = int(data.get("time_limit", 0)) * 60   # minutes → seconds
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid time limit"}), 400

    playlist, total = [], 0
    for song in SONG_LIBRARY:
        if total + song["length"] <= time_limit:
            playlist.append(song)
            total += song["length"]
    return jsonify({"playlist": playlist, "total_length": total})

#Loops through song library and adds songs of a genre
@app.route("/api/playlist/generate-by-genre", methods=["POST"])
def generate_playlist_by_genre():
    if not session.get("logged_in"):
        return jsonify({"error": "Not logged in"}), 401
    genre = request.json.get("genre", "").strip()
    playlist = [s for s in SONG_LIBRARY if s["genre"].lower() == genre.lower()][:5]
    return jsonify({"playlist": playlist})



#Loops through songs and checks for artist name
@app.route("/api/export-artist", methods=["POST"])
def export_artist():
    if not session.get("logged_in"):
        return jsonify({"error": "Not logged in"}), 401
    artist = request.json.get("artist", "").strip()
    songs = [s for s in SONG_LIBRARY if s["artist"].lower() == artist.lower()]
    if not songs:
        return jsonify({"error": "No songs found for that artist"}), 404

    lines = [f"Songs by {artist}", "=" * 40, ""]
    for s in songs:
        mins, secs = divmod(s["length"], 60)
        lines += [
            f"Title:  {s['title']}",
            f"Genre:  {s['genre']}",
            f"Length: {mins}:{secs:02d}",
            "",
        ]
    return jsonify({
        "success":  True,
        "filename": f"{artist}_songs.txt",
        "content":  "\n".join(lines),
    })


@app.route("/api/admin/genres-stats")
def genres_stats():
    if not session.get("logged_in"):
        return jsonify({"error": "Not logged in"}), 401

    stats = {}
    for song in SONG_LIBRARY:
        g = song["genre"]
        if g not in stats:
            stats[g] = {"total": 0, "count": 0}
        stats[g]["total"] += song["length"]
        stats[g]["count"] += 1

    result = []
    for genre, s in stats.items():
        avg = s["total"] / s["count"]
        mins, secs = divmod(round(avg), 60)
        result.append({
            "genre":          genre,
            "average_length": f"{mins}:{secs:02d}",
            "song_count":     s["count"],
        })
    return jsonify(sorted(result, key=lambda x: x["genre"]))

if __name__ == "__main__":
    app.run(debug=True)