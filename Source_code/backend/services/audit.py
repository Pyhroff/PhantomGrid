"""
Security services added by Person 3 (with team sign-off):
  * Tamper-evident audit trail  — hash-chained session_logs
  * Replay-attack detection      — reject verbatim re-submission of a session

Both are pure helpers; the endpoints live in main.py.
"""

import hashlib
import json
import time

# ── Replay detection ────────────────────────────────────────────────────────
# In-memory cache of recently-seen behavioural packages. A genuine session is
# never byte-identical twice (rhythm varies); an exact duplicate = a replay.
_seen = {}
REPLAY_WINDOW_SEC = 300  # 5 minutes


def payload_signature(data) -> str:
    """Stable SHA-256 of the behavioural package (order-independent)."""
    canonical = json.dumps(
        {
            "user_id": data.user_id,
            "decoy_tap_count": data.decoy_tap_count,
            "amount_hesitations": data.amount_hesitations,
            "bene_dwell_ms": data.bene_dwell_ms,
            "amount_iki": list(data.amount_iki),
            "pin_vector": list(data.pin_vector),
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def is_replay(signature: str) -> bool:
    """True if this exact package was seen within the replay window."""
    now = time.time()
    for k in [k for k, t in _seen.items() if now - t > REPLAY_WINDOW_SEC]:
        del _seen[k]
    seen_before = signature in _seen
    _seen[signature] = now
    return seen_before


# ── Tamper-evident hash chain ───────────────────────────────────────────────
def _fmt(x) -> str:
    try:
        return f"{float(x):.4f}"
    except (TypeError, ValueError):
        return str(x)


def row_hash(prev_hash, session_id, user_id, l1, l2, l3, composite, decision, ts_iso) -> str:
    """SHA-256 over (previous hash + this row's immutable fields). Any edit to
    any field — or any earlier row — breaks the chain from that point on."""
    blob = "|".join([
        prev_hash or "GENESIS",
        str(session_id), str(user_id),
        _fmt(l1), _fmt(l2), _fmt(l3), _fmt(composite),
        str(decision), str(ts_iso),
    ])
    return hashlib.sha256(blob.encode()).hexdigest()
