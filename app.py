import os
from datetime import date

from flask import (Flask, render_template, request, redirect,
                   url_for, send_from_directory, flash)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ────────────────── Config ──────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-me-with-something-random"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Folder for selfies
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"png", "jpg", "jpeg"}

db = SQLAlchemy(app)

# ────────────────── DB Model ──────────────────
class Entry(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    log_date  = db.Column(db.Date,   default=date.today, unique=True)
    am_done   = db.Column(db.Boolean, default=False)
    pm_done   = db.Column(db.Boolean, default=False)
    notes     = db.Column(db.Text)
    photo     = db.Column(db.String(200))   # filename or NULL

# ────────────────── Helpers ──────────────────
def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# ────────────────── Routes ──────────────────
@app.route("/")
def home():
    today = Entry.query.filter_by(log_date=date.today()).first()
    return render_template("home.html", today=today)

# ------------ Log routine & upload photo ------------
@app.route("/log", methods=["GET", "POST"])
def log():
    today_entry = Entry.query.filter_by(log_date=date.today()).first()
    if request.method == "POST":
        # Create new or update existing
        am  = bool(request.form.get("am_done"))
        pm  = bool(request.form.get("pm_done"))
        note = request.form.get("notes", "")
        
        if today_entry is None:
            today_entry = Entry(log_date=date.today())
            db.session.add(today_entry)
        
        today_entry.am_done = am
        today_entry.pm_done = pm
        today_entry.notes   = note

        # Handle selfie upload (optional)
        file = request.files.get("photo")
        if file and file.filename and allowed(file.filename):
            fname = f"{date.today()}_{secure_filename(file.filename)}"
            path  = os.path.join(app.config["UPLOAD_FOLDER"], fname)
            file.save(path)
            today_entry.photo = fname
        
        db.session.commit()
        flash("Saved!", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("log.html", entry=today_entry)

# ------------ Show past 30 days ------------
@app.route("/dashboard")
def dashboard():
    entries = (Entry.query
               .order_by(Entry.log_date.desc())
               .limit(30).all())
    return render_template("dashboard.html", entries=entries)

# ------------ Serve uploaded selfies ------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ────────────────── Main ──────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)