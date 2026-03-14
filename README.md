# 🎓 Mentor Portal — Python Flask Version

A full-stack mentor portal using **Python Flask** backend + **Supabase** database.

---

## 📁 Project Structure

```
mentor_portal_flask/
├── app.py              ← Flask backend (all API routes)
├── .env                ← Credentials (Supabase + Email)
├── requirements.txt    ← Python dependencies
├── schema.sql          ← Run this in Supabase ONCE to create tables
└── templates/
    └── index.html      ← Complete frontend (HTML + JS + Tailwind)
```

---

## 🚀 Setup & Run

### Step 1 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Setup Supabase Database (ONE TIME ONLY)

1. Go to https://supabase.com → Your Project → **SQL Editor**
2. Paste the contents of `schema.sql`
3. Click **Run**

### Step 3 — Run the Flask app

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔧 Configuration (.env)

All credentials are already filled in `.env`:

```
SUPABASE_URL=https://fdcxktdnuxpoqlkxihuo.supabase.co
SUPABASE_ANON_KEY=eyJ...
EMAIL=sprithika990@gmail.com
EMAIL_PASSWORD=gieq kvyg cbrk ccyc
SECRET_KEY=mentor-portal-flask-secret-2024
```

---

## ✨ Features

- 🔐 **Sign Up / Sign In** (Supabase Auth)
- 📊 **Dashboard** with live stats (total students, arrears, low CGPA, scholarships)
- ➕ **Add Student** with full personal, parent & academic info
- 📋 **View Students** with search & filter
- 👤 **Student Profile** with detailed view
- ✏️ **Edit Student** details
- 🗑️ **Delete Student** with confirmation
- 📢 **Send Announcement** via email to all students
- ⬇️ **Download CSV** of all students
- ⬇️ **Download Profile** as .txt file

---

## 📧 Email Setup Note

The email uses **Gmail App Password**. If emails aren't sending:
1. Go to your Google Account → Security → 2-Step Verification → App Passwords
2. Create a new App Password and paste it in `.env` as `EMAIL_PASSWORD`

---

## 🛠️ Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port 5000 in use | Run with `python app.py` after changing port in app.py: `port=5001` |
| Supabase auth error | Run `schema.sql` in Supabase SQL Editor first |
| Email not sending | Check Gmail App Password in `.env` |
