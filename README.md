# BloodBank Backend — FastAPI + MySQL

## Setup
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Fill in your values
uvicorn app.main:app --reload
```

## API Docs
Visit: http://localhost:8000/docs

## Project Structure
```
app/
  main.py              # FastAPI app entry point
  core/
    config.py          # Settings from .env
    database.py        # MySQL connection + session
    security.py        # JWT + password utils
  models/
    user.py            # User model
    health.py          # Health declaration model
    donation.py        # Donation record model
    message.py         # Chat message model
    otp.py             # OTP model
  routers/
    auth.py            # Register, Login, OTP, Password
    users.py           # User profiles
    donors.py          # Search, health check, donations
    chat.py            # WebSocket + REST chat
    admin.py           # Admin dashboard
```
