from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

MUSIC_FOLDER = "static/music"

USERNAME = "admin"
PASSWORD = "1234"

#Loops through all songs in the folder and organizes them, extracting the id, name, and file name
def load_tracks():
    mp3_files = sorted([
        f for f in os.listdir(MUSIC_FOLDER)
        if f.endswith(".mp3")
    ])

    return [
        {
            "id": i,
            "name": f[:-4],
            "file": f
        }
        for i, f in enumerate(mp3_files)
    ]


#LOGIN PAGE
@app.route("/")
def login_page():
    if session.get("logged_in"):
        return redirect("/home")

    return render_template("login.html")


# LOGIN HANDLER
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    #Checks if username and password is correct
    if username == USERNAME and password == PASSWORD:
        session["logged_in"] = True
        return redirect("/home")

    #If incorrect, return an error
    return render_template(
        "login.html",
        error="Invalid credentials"
    )


# HOME
@app.route("/home")
def home():

    if not session.get("logged_in"):
        return redirect("/")

    return render_template(
        "index.html",
        tracks=load_tracks()
    )


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# STREAM SONG
@app.route("/track/<int:track_id>")
def get_track(track_id):

    if not session.get("logged_in"):
        return "Unauthorized", 401

    tracks = load_tracks()

    if track_id < 0 or track_id >= len(tracks):
        return "Track not found", 404

    filename = tracks[track_id]["file"]

    return send_from_directory(
        MUSIC_FOLDER,
        filename,
        mimetype="audio/mp3"
    )


# TRACK LIST API
@app.route("/tracks")
def get_tracks():

    if not session.get("logged_in"):
        return jsonify([])

    return jsonify(load_tracks())


if __name__ == "__main__":
    app.run(debug=True)