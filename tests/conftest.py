import pytest
import requests

BASE_URL = "http://localhost:8000"

LEGIT_L3_INTERVALS = [118, 92, 107, 85, 99]
ATTACKER_L3_INTERVALS = [220, 180, 310, 95, 260]
TEST_USER = "test_user"


def check_api_online() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def enroll_test_user():
    if not check_api_online():
        pytest.skip("Backend offline — skipping all integration tests")

    # Enroll Layer 1
    requests.post(f"{BASE_URL}/enroll/layer1", json={
        "user_id": TEST_USER,
        "events": [
            {"decoy_interactions": 0, "hover_hesitation_ms": 120, "familiar_zone_latency_ms": 200},
            {"decoy_interactions": 0, "hover_hesitation_ms": 110, "familiar_zone_latency_ms": 195},
            {"decoy_interactions": 0, "hover_hesitation_ms": 130, "familiar_zone_latency_ms": 210},
        ]
    })

    # Enroll Layer 2
    requests.post(f"{BASE_URL}/enroll/layer2", json={
        "user_id": TEST_USER,
        "events": [
            {"nav_entropy": 0.2, "digit_fluency_gaps_ms": 80, "beneficiary_dwell_ms": 600},
            {"nav_entropy": 0.22, "digit_fluency_gaps_ms": 85, "beneficiary_dwell_ms": 620},
            {"nav_entropy": 0.19, "digit_fluency_gaps_ms": 78, "beneficiary_dwell_ms": 590},
        ]
    })

    # Enroll Layer 3
    requests.post(f"{BASE_URL}/enroll/layer3", json={
        "user_id": TEST_USER,
        "intervals": LEGIT_L3_INTERVALS
    })
