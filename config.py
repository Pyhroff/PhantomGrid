# PhantomGrid — Central Configuration
# All demo scripts, tests, and dashboard read from this file.
# Local-only — the hackathon's Railway deployment is no longer running.

BASE_URL = "http://localhost:8000"
DEMO_USER = "demo_user"

# Representative legitimate PIN inter-keystroke intervals (ms) used by demo scripts.
LEGIT_INTERVALS = [112, 98, 105, 89, 103]

# Divergent intervals used by demo_attacker.py to simulate an impostor.
ATTACKER_INTERVALS = [220, 180, 310, 95, 260]
