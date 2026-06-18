# ── PhantomGrid config ────────────────────────────────────────────────────
# Change BASE_URL to Person 2's ngrok/Railway URL before demo day.
# Everything else (scripts, tests, dashboard) reads from here.

BASE_URL = "http://localhost:8000"   # e.g. "https://abc123.ngrok-free.app"
DEMO_USER = "demo_user"

# Your enrolled PIN rhythm baseline (ms between keypresses for a 5-digit PIN).
# Run enroll.py first — it uses these as the centre of your training distribution.
LEGIT_INTERVALS = [112, 98, 105, 89, 103]

# Attacker rhythm — deliberately divergent, guaranteed Red.
ATTACKER_INTERVALS = [220, 180, 310, 95, 260]
