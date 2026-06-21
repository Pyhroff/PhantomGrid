import sqlite3
import pytest
import requests

BASE_URL = "http://localhost:8000"

LEGIT_L3_INTERVALS = [118, 92, 107, 85, 99]
ATTACKER_L3_INTERVALS = [220, 180, 310, 95, 260]
TEST_USER = "test_user"


# ---------------------------------------------------------------------------
# Layer 3 — RhythmLock
# ---------------------------------------------------------------------------

def test_layer3_legit_scores_green():
    r = requests.post(f"{BASE_URL}/score/layer3", json={
        "user_id": TEST_USER,
        "intervals": [int(v * 1.05) for v in LEGIT_L3_INTERVALS]  # ±5% jitter
    })
    assert r.status_code == 200
    data = r.json()
    assert data["score"] < 60, f"Expected green (<60), got {data['score']}"
    assert data["decision"] == "green"


def test_layer3_attacker_scores_red():
    r = requests.post(f"{BASE_URL}/score/layer3", json={
        "user_id": TEST_USER,
        "intervals": ATTACKER_L3_INTERVALS
    })
    assert r.status_code == 200
    data = r.json()
    assert data["score"] >= 85, f"Expected red (>=85), got {data['score']}"
    assert data["decision"] == "red"


# ---------------------------------------------------------------------------
# Layer 2 — Navigation behaviour
# ---------------------------------------------------------------------------

def test_layer2_high_entropy_scores_amber_or_red():
    r = requests.post(f"{BASE_URL}/score/layer2", json={
        "user_id": TEST_USER,
        "nav_entropy": 0.85,
        "digit_fluency_gaps_ms": 420,
        "beneficiary_dwell_ms": 2200
    })
    assert r.status_code == 200
    data = r.json()
    assert data["score"] >= 60, f"Expected amber/red (>=60), got {data['score']}"


# ---------------------------------------------------------------------------
# Layer 1 — Decoy interactions
# ---------------------------------------------------------------------------

def test_layer1_decoy_interaction_flags():
    r = requests.post(f"{BASE_URL}/score/layer1", json={
        "user_id": TEST_USER,
        "decoy_interactions": 3,
        "hover_hesitation_ms": 350,
        "familiar_zone_latency_ms": 800
    })
    assert r.status_code == 200
    data = r.json()
    assert data["score"] >= 60, f"Expected amber/red (>=60), got {data['score']}"


# ---------------------------------------------------------------------------
# Composite fusion — math verification
# ---------------------------------------------------------------------------

def test_composite_fusion_weights():
    # All 50 → composite must be exactly 50.0 (L1×0.30 + L2×0.40 + L3×0.30)
    r = requests.post(f"{BASE_URL}/risk/composite", json={
        "user_id": TEST_USER,
        "layer1_score": 50,
        "layer2_score": 50,
        "layer3_score": 50
    })
    assert r.status_code == 200
    composite = r.json()["composite_score"]
    assert abs(composite - 50.0) <= 0.5, f"Expected 50.0, got {composite}"

    # L1=100, L2=0, L3=0 → 100×0.30 + 0 + 0 = 30.0
    r2 = requests.post(f"{BASE_URL}/risk/composite", json={
        "user_id": TEST_USER,
        "layer1_score": 100,
        "layer2_score": 0,
        "layer3_score": 0
    })
    assert r2.status_code == 200
    composite2 = r2.json()["composite_score"]
    assert abs(composite2 - 30.0) <= 0.5, f"Expected 30.0, got {composite2}"


# ---------------------------------------------------------------------------
# End-to-end sessions
# ---------------------------------------------------------------------------

def test_composite_green_end_to_end():
    l1 = requests.post(f"{BASE_URL}/score/layer1", json={
        "user_id": TEST_USER,
        "decoy_interactions": 0,
        "hover_hesitation_ms": 115,
        "familiar_zone_latency_ms": 198
    }).json()["score"]

    l2 = requests.post(f"{BASE_URL}/score/layer2", json={
        "user_id": TEST_USER,
        "nav_entropy": 0.21,
        "digit_fluency_gaps_ms": 82,
        "beneficiary_dwell_ms": 610
    }).json()["score"]

    l3 = requests.post(f"{BASE_URL}/score/layer3", json={
        "user_id": TEST_USER,
        "intervals": [int(v * 1.03) for v in LEGIT_L3_INTERVALS]
    }).json()["score"]

    r = requests.post(f"{BASE_URL}/risk/composite", json={
        "user_id": TEST_USER,
        "layer1_score": l1,
        "layer2_score": l2,
        "layer3_score": l3
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] == "green", (
        f"Expected green end-to-end, got {data['decision']} (composite={data['composite_score']})"
    )


def test_composite_red_end_to_end():
    """Demo scenario — attacker session must reliably hit Red."""
    l1 = requests.post(f"{BASE_URL}/score/layer1", json={
        "user_id": TEST_USER,
        "decoy_interactions": 4,
        "hover_hesitation_ms": 500,
        "familiar_zone_latency_ms": 1200
    }).json()["score"]

    l2 = requests.post(f"{BASE_URL}/score/layer2", json={
        "user_id": TEST_USER,
        "nav_entropy": 0.9,
        "digit_fluency_gaps_ms": 600,
        "beneficiary_dwell_ms": 3000
    }).json()["score"]

    l3 = requests.post(f"{BASE_URL}/score/layer3", json={
        "user_id": TEST_USER,
        "intervals": ATTACKER_L3_INTERVALS
    }).json()["score"]

    r = requests.post(f"{BASE_URL}/risk/composite", json={
        "user_id": TEST_USER,
        "layer1_score": l1,
        "layer2_score": l2,
        "layer3_score": l3
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] == "red", (
        f"Expected red end-to-end, got {data['decision']} (composite={data['composite_score']})"
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_api_rejects_missing_user_id():
    r = requests.post(f"{BASE_URL}/score/layer3", json={
        "intervals": LEGIT_L3_INTERVALS
        # user_id intentionally omitted
    })
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}"


# ---------------------------------------------------------------------------
# Session log persistence
# ---------------------------------------------------------------------------

def test_session_log_written_after_composite():
    import time
    before = time.time()

    l1 = requests.post(f"{BASE_URL}/score/layer1", json={
        "user_id": TEST_USER,
        "decoy_interactions": 0,
        "hover_hesitation_ms": 120,
        "familiar_zone_latency_ms": 200
    }).json()["score"]

    l2 = requests.post(f"{BASE_URL}/score/layer2", json={
        "user_id": TEST_USER,
        "nav_entropy": 0.2,
        "digit_fluency_gaps_ms": 80,
        "beneficiary_dwell_ms": 600
    }).json()["score"]

    l3 = requests.post(f"{BASE_URL}/score/layer3", json={
        "user_id": TEST_USER,
        "intervals": LEGIT_L3_INTERVALS
    }).json()["score"]

    requests.post(f"{BASE_URL}/risk/composite", json={
        "user_id": TEST_USER,
        "layer1_score": l1,
        "layer2_score": l2,
        "layer3_score": l3
    })

    # Check SQLite directly — DB must be at project root
    conn = sqlite3.connect("phantomgrid.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, composite_score FROM session_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
        (TEST_USER,)
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None, "No session log row found after /risk/composite"
    assert row[0] == TEST_USER
