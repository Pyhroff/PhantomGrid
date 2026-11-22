"""
PhantomGrid – Person 3 test configuration.

All fixtures use uuid-based user_ids (fresh_user) so tests are fully isolated —
no test can pollute another's baseline.  Enrollment uses 5 samples with deliberate
natural variance; identical samples degenerate the IsolationForest.
"""

import pytest
import requests
import subprocess
import tempfile
import time
import urllib.parse
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.getenv("PHANTOMGRID_TEST_URL", "http://127.0.0.1:8000")

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


def _start_local_backend():
    """Start the FastAPI backend on the port in BASE_URL, using a throw-away SQLite file.

    Returns (process, tempdir) or None if the URL is not a local one.
    """
    parsed = urllib.parse.urlparse(BASE_URL)
    if parsed.hostname not in ("127.0.0.1", "localhost"):
        return None
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmp = tempfile.TemporaryDirectory(prefix="phantomgrid-test-")
    env = {**os.environ, "SQLITE_PATH": os.path.join(tmp.name, "test.db")}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", str(parsed.port or 8000)],
        cwd=os.path.join(root, "backend"), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return proc, tmp


@pytest.fixture(scope="session", autouse=True)
def require_backend():
    """Use a running backend if there is one; otherwise start one for this test session."""
    if _api_online():
        yield
        return
    started = _start_local_backend()
    if started is None:
        pytest.skip(f"Backend at {BASE_URL} is offline and cannot be started locally")
    proc, tmp = started
    try:
        deadline = time.time() + 30
        while time.time() < deadline and not _api_online():
            if proc.poll() is not None:
                break
            time.sleep(0.5)
        if not _api_online():
            pytest.skip("Backend did not start (are the requirements installed?)")
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        tmp.cleanup()


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
