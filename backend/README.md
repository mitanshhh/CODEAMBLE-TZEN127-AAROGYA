# Aarogya Backend Engine

A high-performance, modular FastAPI backend service for the Healthcare & Facility Operations System.

## Features

- **FastAPI** with async architecture
- **SQLAlchemy** with Neon DB (Serverless PostgreSQL)
- **Role-Based Access Control (RBAC)** via JWT tokens
- **Secure File Serving** for PDF reports
- **AI Analytics** via Google Gemini
- **Multilingual Support** via Google Cloud Translation API

## Setup Instructions

1. **Clone the repository and cd into the backend folder.**
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in the required variables (specifically `DATABASE_URL` if not already set, and `GEMINI_API_KEY`, `SMTP_EMAIL`, `SMTP_PASSWORD`).
   *Note: In production, secrets should go through a Secret Manager (e.g., GCP Secret Manager), not a checked-in `.env` file.*

5. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the Server:**
   ```bash
   fastapi dev app/main.py
   ```

The API docs will be available at `http://127.0.0.1:8000/docs`.

## Deferred / Simplified for Hackathon

- **Google Calendar Integration:** Removed entirely as per user instructions.
- **Passwords:** A random password generation strategy is kept simple, but uses standard `bcrypt` hashing for verification.
- **SMTP Verification:** Error handling for SMTP failures is kept to a print statement so it won't crash user creation if credentials are not configured.
- **Audit Logs on GET:** Audit logging is implemented for creating, updating, and viewing individual patient records, but not for the paginated list endpoint to prevent log bloat.
