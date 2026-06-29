"""
PhantomGrid – Person 3 test configuration.

All fixtures use uuid-based user_ids (fresh_user) so tests are fully isolated —
no test can pollute another's baseline.  Enrollment uses 5 samples with deliberate
natural variance; identical samples degenerate the IsolationForest.
"""

import pytest
import requests
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:8000"

ENROLL_TIMEOUT = 30
VERIFY_TIMEOUT = 30

# PIN rhythm vectors
LEGIT_PIN      = [118, 92, 107, 85, 99]
DIVERGENT_PIN  = [400, 350, 500, 300, 450]

# Full verify payloads (user_id is injected by verify() helper)
LEGIT_VERIFY = {
    "decoy_tap_count":    0,
    "amount_hesitations": 0,
    "bene_dwell_ms":      600,
    "amount_iki":         [110, 95, 105],
    "pin_vector":         LEGIT_PIN,
}

ATTACKER_VERIFY = {
    "decoy_tap_count":    5,
    "amount_hesitations": 5,
    "bene_dwell_ms":      4000,
    "amount_iki":         [600, 650, 700],
    "pin_vector":         DIVERGENT_PIN,
}


def _api_online() -> bool:
    try:
        return requests.get(f"{BASE_URL}/docs", timeout=3).status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def require_backend():
    if not _api_online():
        pytest.skip("Backend offline — skipping all integration tests")


@pytest.fixture(scope="function")
def fresh_user():
    """Unique user_id per test, pre-enrolled. Prevents cross-test baseline pollution."""
    uid = f"t_{uuid.uuid4().hex[:8]}"
    enroll_user(uid)
    return uid


def enroll_user(user_id: str) -> None:
    """POST 5 varied enrollment samples via /enroll.

    Natural variance is critical — identical samples degenerate IsolationForest,
    collapsing all scores near 45 regardless of behaviour.
    """
    samples = [
        {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 600,
         "amount_iki": [110, 95, 105], "pin_vector": [118, 92, 107, 85, 99]},
        {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 622,
         "amount_iki": [108, 98, 102], "pin_vector": [122, 88, 110, 82, 102]},
        {"decoy_tap_count": 0, "amount_hesitations": 1, "bene_dwell_ms": 578,
         "amount_iki": [115, 92, 108], "pin_vector": [115, 95, 104, 88,  96]},
        {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 611,
         "amount_iki": [112, 96, 106], "pin_vector": [120, 90, 108, 86, 100]},
        {"decoy_tap_count": 1, "amount_hesitations": 0, "bene_dwell_ms": 593,
         "amount_iki": [109, 94, 107], "pin_vector": [116, 93, 105, 87,  98]},
    ]
    for s in samples:
        r = requests.post(
            f"{BASE_URL}/enroll",
            json={"user_id": user_id, **s},
            timeout=ENROLL_TIMEOUT,
        )
        assert r.status_code == 200, f"/enroll failed ({r.status_code}): {r.text}"


def verify(user_id: str, payload: dict) -> dict:
    r = requests.post(
        f"{BASE_URL}/verify",
        json={"user_id": user_id, **payload},
        timeout=VERIFY_TIMEOUT,
    )
    assert r.status_code == 200, f"/verify failed ({r.status_code}): {r.text}"
    return r.json()
