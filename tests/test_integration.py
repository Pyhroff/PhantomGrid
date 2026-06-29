"""
PhantomGrid — Person 3 integration tests.

Run:  pytest tests/ -v        (with the backend running on 127.0.0.1:8000)

These assertions are anchored on EMPIRICALLY OBSERVED backend behavior with the
CONTINUOUS scoring engine (services/scoring.py) and updated bands
(ALLOW <60 · OTP 60–79 · BLOCK ≥80). Confirmed values against the live backend:

    legit verify            -> L1=4.4  L2=1.4  L3=0.0   comp=1.9   ALLOW
    mild attacker           -> L1=64.6 L2=100  L3=42.0  comp=72.0  OTP
    hard/extreme attacker   -> L1=100  L2=100  L3=100   comp=100   BLOCK
    attacker after a legit  -> L1=100  L2=100  L3=100   comp=100   BLOCK  (robust now)
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conftest import (  # noqa: E402
    BASE_URL, LEGIT_PIN, DIVERGENT_PIN,
    LEGIT_VERIFY, ATTACKER_VERIFY,
    enroll_user, verify,
)


# ---------------------------------------------------------------------------
# Layer-level behavior
# ---------------------------------------------------------------------------

def test_legit_session_allows(fresh_user):
    """A user behaving like their baseline scores low on all layers -> ALLOW."""
    r = verify(fresh_user, LEGIT_VERIFY)
    assert r["decision"] == "ALLOW", r
    assert r["composite_score"] < 60
    assert r["layer3_score"] <= 10  # PIN rhythm matches baseline (continuous DTW ~0)


def test_clean_attacker_blocks(fresh_user):
    """THE DEMO SCENARIO: a fresh-enrolled account, attacker verifies FIRST.
    Divergent decoys + PIN rhythm push L1 and L3 to 95 -> composite 85 -> BLOCK."""
    r = verify(fresh_user, ATTACKER_VERIFY)
    assert r["decision"] == "BLOCK", (
        f"Attacker must BLOCK on a clean account, got {r}. "
        "If this fails, the account baseline was polluted by a prior ALLOW."
    )
    assert r["composite_score"] >= 80


def test_layer3_rhythm_mismatch_is_high(fresh_user):
    """RhythmLock: a divergent PIN rhythm scores high on Layer 3."""
    r = verify(fresh_user, dict(LEGIT_VERIFY, pin_vector=DIVERGENT_PIN))
    assert r["layer3_score"] >= 70, r


def test_layer1_decoy_taps_flag(fresh_user):
    """CognitiveTrap: tapping decoys pushes Layer 1 high."""
    r = verify(fresh_user, dict(LEGIT_VERIFY, decoy_tap_count=5, amount_hesitations=5))
    assert r["layer1_score"] >= 70, r


# ---------------------------------------------------------------------------
# Adaptive-learning pollution (documents the demo landmine)
# ---------------------------------------------------------------------------

def test_attacker_blocks_even_after_legit_session(fresh_user):
    """With the continuous scoring engine the demo is order-independent: a legit
    ALLOW (which appends to the baseline via adaptive learning) no longer
    suppresses a strong attacker. The attacker still BLOCKs on the same user.
    (Under the OLD bucketed scoring this dropped to OTP — see CHANGELOG.)"""
    legit = verify(fresh_user, LEGIT_VERIFY)
    assert legit["decision"] == "ALLOW"

    attacker = verify(fresh_user, ATTACKER_VERIFY)
    assert attacker["decision"] == "BLOCK", attacker
    assert attacker["composite_score"] >= 80


# ---------------------------------------------------------------------------
# Fusion math (pure function, no endpoint needed)
# ---------------------------------------------------------------------------

def test_fusion_weights_and_thresholds():
    import importlib.util
    backend = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
    spec = importlib.util.spec_from_file_location("fusion", os.path.join(backend, "services", "fusion.py"))
    fusion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fusion)

    # L1*0.30 + L2*0.40 + L3*0.30
    assert abs(fusion.fusion_score(50, 50, 50)["composite_score"] - 50.0) < 0.5
    assert abs(fusion.fusion_score(100, 0, 0)["composite_score"] - 30.0) < 0.5
    # Updated bands: ALLOW <60 · OTP 60-79 · BLOCK >=80
    assert fusion.fusion_score(10, 10, 10)["decision"]   == "ALLOW"   # 10  -> ALLOW
    assert fusion.fusion_score(50, 50, 50)["decision"]   == "ALLOW"   # 50  -> ALLOW (was OTP)
    assert fusion.fusion_score(60, 60, 60)["decision"]   == "OTP"     # 60  -> OTP
    assert fusion.fusion_score(70, 70, 70)["decision"]   == "OTP"     # 70  -> OTP
    assert fusion.fusion_score(80, 80, 80)["decision"]   == "BLOCK"   # 80  -> BLOCK
    assert fusion.fusion_score(100, 100, 100)["decision"] == "BLOCK"  # 100 -> BLOCK


# ---------------------------------------------------------------------------
# Validation + persistence
# ---------------------------------------------------------------------------

def test_verify_rejects_missing_user_id():
    r = requests.post(f"{BASE_URL}/verify", json={
        "decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 600,
        "amount_iki": [100], "pin_vector": LEGIT_PIN,
    })
    assert r.status_code == 422


def test_session_logged_after_verify(fresh_user):
    """Every /verify writes a row; confirm it appears in GET /logs."""
    verify(fresh_user, LEGIT_VERIFY)
    logs = requests.get(f"{BASE_URL}/logs", timeout=5).json()
    assert isinstance(logs, list) and len(logs) >= 1
    mine = [row for row in logs if row["user_id"] == fresh_user]
    assert mine, f"No /logs row for {fresh_user}"
    row = mine[0]
    for key in ("session_id", "timestamp", "layer1_score", "layer2_score",
                "layer3_score", "composite_score", "decision"):
        assert key in row
