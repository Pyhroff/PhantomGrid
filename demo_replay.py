"""
PhantomGrid — DEMO: Replay-Attack Defense.

Shows that capturing a legit session and replaying it verbatim does NOT work:
a genuine session is never byte-identical twice, so an exact duplicate is
detected as a replay and forced to BLOCK.

    python demo_replay.py
"""

import sys
import uuid
import requests

try:
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


def main():
    user = f"replay_demo_{uuid.uuid4().hex[:4]}"
    print(f"\n  PhantomGrid — REPLAY-ATTACK DEMO   (backend: {BASE_URL})")
    print(f"  Account: {user}\n")

    try:
        for s in ENROLL:
            requests.post(f"{BASE_URL}/enroll", json=dict(s, user_id=user), timeout=30)
    except Exception as e:
        print(f"  ✗ Backend unreachable: {e}")
        sys.exit(1)
    print("   baseline enrolled (5 samples)")

    # The attacker has sniffed this exact legit package off the wire.
    captured = {
        "user_id": user, "decoy_tap_count": 0, "amount_hesitations": 0,
        "bene_dwell_ms": 605, "amount_iki": [111, 94, 106], "pin_vector": [118, 92, 107, 86, 99],
    }

    print("\n  [1] Genuine session runs...")
    r1 = requests.post(f"{BASE_URL}/verify", json=captured, timeout=30).json()
    print(f"      decision = {r1['decision']}   replay_detected = {r1['replay_detected']}")

    print("\n  [2] Attacker REPLAYS the captured packet verbatim...")
    r2 = requests.post(f"{BASE_URL}/verify", json=captured, timeout=30).json()
    print(f"      decision = {r2['decision']}   replay_detected = {r2['replay_detected']}")

    print()
    if r2["replay_detected"] and r2["decision"] == "BLOCK":
        print("   🛡 Replay detected and BLOCKED. A captured session can't be reused.\n")
    else:
        print(f"   ⚠ Expected a blocked replay, got {r2}.\n")


if __name__ == "__main__":
    main()
