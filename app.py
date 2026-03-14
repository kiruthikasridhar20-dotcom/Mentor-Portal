from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mentor-portal-secret-2024")
CORS(app)

# Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Email config
EMAIL_USER = os.environ.get("EMAIL")
EMAIL_PASS = os.environ.get("EMAIL_PASSWORD")


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_supabase_with_token(token: str) -> Client:
    """Return a Supabase client authenticated with the user's JWT."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.auth.set_session(token, "")
    return client


# ─── Page Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── Auth API ─────────────────────────────────────────────────────────────────

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not all([email, password, full_name]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            user_id = res.user.id
            # Insert into mentors table
            supabase.table("mentors").insert({
                "id": user_id,
                "email": email,
                "full_name": full_name
            }).execute()
            return jsonify({
                "user": {"id": user_id, "email": email},
                "access_token": res.session.access_token if res.session else None,
                "full_name": full_name
            })
        return jsonify({"error": "Signup failed"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/auth/signin", methods=["POST"])
def signin():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user and res.session:
            # Fetch mentor profile
            mentor = supabase.table("mentors").select("*").eq("id", res.user.id).maybe_single().execute()
            return jsonify({
                "user": {"id": res.user.id, "email": res.user.email},
                "access_token": res.session.access_token,
                "full_name": mentor.data["full_name"] if mentor.data else email
            })
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 401


# ─── Students API ─────────────────────────────────────────────────────────────

def auth_header():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return token


@app.route("/api/students", methods=["GET"])
def get_students():
    token = auth_header()
    try:
        client = get_supabase_with_token(token)
        res = client.table("students").select("*").order("created_at", desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/students", methods=["POST"])
def add_student():
    token = auth_header()
    data = request.get_json()
    try:
        client = get_supabase_with_token(token)
        user = client.auth.get_user(token)
        data["mentor_id"] = user.user.id
        data["cgpa"] = float(data.get("cgpa", 0))
        data["gpa"] = float(data.get("gpa", 0))
        res = client.table("students").insert(data).execute()
        return jsonify(res.data[0] if res.data else {}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/students/<student_id>", methods=["GET"])
def get_student(student_id):
    token = auth_header()
    try:
        client = get_supabase_with_token(token)
        res = client.table("students").select("*").eq("id", student_id).maybe_single().execute()
        if res.data:
            return jsonify(res.data)
        return jsonify({"error": "Student not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/students/<student_id>", methods=["PUT"])
def update_student(student_id):
    token = auth_header()
    data = request.get_json()
    try:
        client = get_supabase_with_token(token)
        data["cgpa"] = float(data.get("cgpa", 0))
        data["gpa"] = float(data.get("gpa", 0))
        # Remove fields that shouldn't be updated
        data.pop("id", None)
        data.pop("mentor_id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
        res = client.table("students").update(data).eq("id", student_id).execute()
        return jsonify(res.data[0] if res.data else {})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/students/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    token = auth_header()
    try:
        client = get_supabase_with_token(token)
        client.table("students").delete().eq("id", student_id).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/stats", methods=["GET"])
def get_stats():
    token = auth_header()
    try:
        client = get_supabase_with_token(token)
        res = client.table("students").select("*").execute()
        students = res.data or []
        return jsonify({
            "totalStudents": len(students),
            "studentsWithArrears": len([s for s in students if s.get("arrears_details", "").strip()]),
            "lowCGPAStudents": len([s for s in students if float(s.get("cgpa", 0)) < 7.0]),
            "scholarshipStudents": len([s for s in students if s.get("scholarship_details", "").strip()])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ─── Announcement / Email API ─────────────────────────────────────────────────

@app.route("/api/announcement", methods=["POST"])
def send_announcement():
    data = request.get_json()
    message = data.get("message", "")
    token = auth_header()

    if not message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400

    try:
        # Fetch all students for this mentor
        client = get_supabase_with_token(token)
        res = client.table("students").select("email, student_name").execute()
        students = res.data or []

        if not students:
            return jsonify({"error": "No students found to send announcement"}), 404

        # Send email to each student
        sent = 0
        errors = []
        for student in students:
            try:
                send_email(
                    to=student["email"],
                    subject="📢 New Announcement from Your Mentor",
                    body=f"Dear {student['student_name']},\n\n{message}\n\nRegards,\nYour Mentor"
                )
                sent += 1
            except Exception as e:
                errors.append(f"{student['email']}: {str(e)}")

        return jsonify({
            "success": True,
            "sent": sent,
            "total": len(students),
            "errors": errors
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(to: str, subject: str, body: str):
    if not EMAIL_USER or not EMAIL_PASS:
        raise Exception("Email credentials not configured in .env")

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to, msg.as_string())


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
