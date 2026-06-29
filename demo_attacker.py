"""
PhantomGrid — DEMO BACKUP: attacker scenario (guaranteed BLOCK).

Run this if live keyboard input fumbles on stage. It enrolls a fresh victim
account with a legit baseline, then submits an ATTACKER session (decoy taps +
divergent PIN rhythm) and prints the result. Watch the analyst dashboard light
up red as it runs.

    python demo_attacker.py

The dashboard shows the new row immediately (it polls GET /logs every 2s).
"""

import sys
import uuid
import requests

try:                                     # make emoji/arrows safe on Windows consoles
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from config import BASE_URL          # picks up ngrok/Railway host if you changed it
except Exception:
    BASE_URL = "http://127.0.0.1:8000"

# Legit baseline for the victim account (5 varied samples)
ENROLL = [
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 600, "amount_iki": [110, 95, 105], "pin_vector": [118, 92, 107, 85, 99]},
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 620, "amount_iki": [115, 90, 100], "pin_vector": [120, 90, 108, 86, 100]},
    {"decoy_tap_count": 0, "amount_hesitations": 1, "bene_dwell_ms": 580, "amount_iki": [108, 98, 102], "pin_vector": [116, 94, 105, 84, 98]},
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 640, "amount_iki": [112, 93, 107], "pin_vector": [119, 91, 106, 85, 99]},
    {"decoy_tap_count": 1, "amount_hesitations": 0, "bene_dwell_ms": 600, "amount_iki": [110, 96, 104], "pin_vector": [117, 93, 107, 86, 99]},
]

# Attacker: taps decoys, hesitates, and types the PIN with a totally different rhythm
ATTACKER = {
    "decoy_tap_count": 6,
    "amount_hesitations": 6,
    "bene_dwell_ms": 4500,
    "amount_iki": [650, 700, 680],
    "pin_vector": [420, 360, 520, 310, 470],
}


def main():
    user = f"attacker_demo_{uuid.uuid4().hex[:4]}"
    print(f"\n  PhantomGrid — ATTACKER DEMO   (backend: {BASE_URL})")
    print(f"  Victim account: {user}\n")

    try:
        for i, s in enumerate(ENROLL, 1):
            requests.post(f"{BASE_URL}/enroll", json=dict(s, user_id=user), timeout=30)
            print(f"   enrolled legit baseline sample {i}/5")
    except Exception as e:
        print(f"\n  ✗ Could not reach backend at {BASE_URL}: {e}")
        sys.exit(1)

    print("\n  >>> Attacker uses the account (decoys tapped, wrong PIN rhythm)...")
    r = requests.post(f"{BASE_URL}/verify", json=dict(ATTACKER, user_id=user), timeout=30).json()

    print(f"\n   L1 (CognitiveTrap) : {r['layer1_score']}")
    print(f"   L2 (IntentTrace)   : {r['layer2_score']}")
    print(f"   L3 (RhythmLock)    : {r['layer3_score']}")
    print(f"   COMPOSITE          : {r['composite_score']}")
    print(f"\n   DECISION → {r['decision']}")
    if r["decision"] == "BLOCK":
        print("   ⛔ Transaction blocked. Stolen credentials were not enough.\n")
    else:
        print(f"   ⚠ Expected BLOCK, got {r['decision']} — check backend scoring.\n")


if __name__ == "__main__":
    main()
