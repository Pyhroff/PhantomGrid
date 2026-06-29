"""
PhantomGrid — DEMO BACKUP: legitimate scenario (guaranteed ALLOW).

Enrolls a fresh account with a baseline and then submits a matching legit
session. Use it to show the green/ALLOW path on the dashboard.

    python demo_legit.py
"""

import sys
import uuid
import requests

try:                                     # make emoji/arrows safe on Windows consoles
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from config import BASE_URL
except Exception:
    BASE_URL = "http://127.0.0.1:8000"

ENROLL = [
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 600, "amount_iki": [110, 95, 105], "pin_vector": [118, 92, 107, 85, 99]},
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 620, "amount_iki": [115, 90, 100], "pin_vector": [120, 90, 108, 86, 100]},
    {"decoy_tap_count": 0, "amount_hesitations": 1, "bene_dwell_ms": 580, "amount_iki": [108, 98, 102], "pin_vector": [116, 94, 105, 84, 98]},
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 640, "amount_iki": [112, 93, 107], "pin_vector": [119, 91, 106, 85, 99]},
    {"decoy_tap_count": 1, "amount_hesitations": 0, "bene_dwell_ms": 600, "amount_iki": [110, 96, 104], "pin_vector": [117, 93, 107, 86, 99]},
]

LEGIT = {
    "decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 605,
    "amount_iki": [111, 94, 106], "pin_vector": [118, 92, 107, 86, 99],
}


def main():
    user = f"legit_demo_{uuid.uuid4().hex[:4]}"
    print(f"\n  PhantomGrid — LEGIT DEMO   (backend: {BASE_URL})")
    print(f"  Account: {user}\n")
    try:
        for i, s in enumerate(ENROLL, 1):
            requests.post(f"{BASE_URL}/enroll", json=dict(s, user_id=user), timeout=30)
            print(f"   enrolled baseline sample {i}/5")
    except Exception as e:
        print(f"\n  ✗ Could not reach backend at {BASE_URL}: {e}")
        sys.exit(1)

    print("\n  >>> Genuine account holder completes a payment...")
    r = requests.post(f"{BASE_URL}/verify", json=dict(LEGIT, user_id=user), timeout=30).json()
    print(f"\n   L1 {r['layer1_score']} · L2 {r['layer2_score']} · L3 {r['layer3_score']} · COMPOSITE {r['composite_score']}")
    print(f"\n   DECISION → {r['decision']}")
    print("   ✅ Session proceeds with zero friction.\n" if r["decision"] == "ALLOW"
          else f"   ⚠ Expected ALLOW, got {r['decision']}.\n")


if __name__ == "__main__":
    main()
