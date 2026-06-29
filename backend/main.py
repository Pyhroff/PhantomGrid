import json

from datetime import datetime
from uuid import uuid4

from typing import Optional
from fastapi import FastAPI, Query
from sqlalchemy import inspect, text

from database import engine
from database import SessionLocal

import database_models

from schemas import (
    EnrollmentRequest,
    VerificationRequest,
    EnrollL1Request,
    EnrollL2Request,
    EnrollL3Request,
    ScoreL1Request,
    ScoreL2Request,
    ScoreL3Request,
    CompositeRequest,
)

from services.layer3 import (
    calculate_distance,
    get_layer3_risk,
)
from services.layer1 import get_layer1_risk
from services.layer2 import get_layer2_risk
from services.scoring import continuous_if_risk, _normalized_deviation
from services.fusion import fusion_score
from services import audit


app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

database_models.Base.metadata.create_all(
    bind=engine
)

# Lightweight migration: add audit-chain columns to existing databases
# (create_all only creates missing TABLES, not missing COLUMNS).
def _migrate_audit_columns():
    existing = [c["name"] for c in inspect(engine).get_columns("session_logs")]
    with engine.connect() as conn:
        for col in ("row_hash", "prev_hash"):
            if col not in existing:
                conn.execute(text(f"ALTER TABLE session_logs ADD COLUMN {col} VARCHAR"))
        conn.commit()

def _migrate_profile_columns():
    existing = [c["name"] for c in inspect(engine).get_columns("user_profiles")]
    with engine.connect() as conn:
        for col in ("l1_baseline", "l2_baseline", "l3_baseline"):
            if col not in existing:
                conn.execute(text(f"ALTER TABLE user_profiles ADD COLUMN {col} VARCHAR"))
        conn.commit()

_migrate_audit_columns()
_migrate_profile_columns()


_SEED_SAMPLES = [
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 600,
     "amount_iki": [110, 95, 105], "pin_vector": [118, 92, 107, 85, 99]},
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 622,
     "amount_iki": [108, 98, 102], "pin_vector": [122, 88, 110, 82, 102]},
    {"decoy_tap_count": 0, "amount_hesitations": 1, "bene_dwell_ms": 578,
     "amount_iki": [115, 92, 108], "pin_vector": [115, 95, 104, 88, 96]},
    {"decoy_tap_count": 0, "amount_hesitations": 0, "bene_dwell_ms": 611,
     "amount_iki": [112, 96, 106], "pin_vector": [120, 90, 108, 86, 100]},
    {"decoy_tap_count": 1, "amount_hesitations": 0, "bene_dwell_ms": 593,
     "amount_iki": [109, 94, 107], "pin_vector": [116, 93, 105, 87, 98]},
]


def _seed_user(user_id: str):
    """Pre-enroll a user with a synthetic legitimate baseline if not already enrolled."""
    db = SessionLocal()
    existing = db.query(database_models.UserProfile).filter(
        database_models.UserProfile.user_id == user_id
    ).first()
    if existing:
        db.close()
        return
    l1_vecs, l2_vecs, pin_vecs = [], [], []
    for s in _SEED_SAMPLES:
        avg_iki = sum(s["amount_iki"]) / len(s["amount_iki"])
        l1_vecs.append([s["decoy_tap_count"], s["amount_hesitations"]])
        l2_vecs.append([s["bene_dwell_ms"], avg_iki])
        pin_vecs.append(s["pin_vector"])
    profile = database_models.UserProfile(
        user_id=user_id,
        layer1_vectors=json.dumps(l1_vecs),
        layer2_vectors=json.dumps(l2_vecs),
        pin_vectors=json.dumps(pin_vecs),
    )
    db.add(profile)
    db.commit()
    db.close()
    print(f"[PhantomGrid] {user_id} seeded successfully")


# Seed demo_user and legit_user with synthetic baseline for live API testing.
# arjun_4821 is NOT seeded here — must be enrolled via bank UI (Nexa_bank_demoUI.html?enroll=true)
# so real PIN rhythm and bene_dwell signals build the actual baseline.
for _uid in ("demo_user", "legit_user"):
    _seed_user(_uid)

print(
    inspect(engine).get_table_names()
)
   
#Enrollment Endpoint
@app.post("/enroll")
def enroll(
    data: EnrollmentRequest
):

    db = SessionLocal()

    avg_amount_iki = (
        sum(data.amount_iki)
        / len(data.amount_iki)
    )

    layer1_vector = [

        data.decoy_tap_count,

        data.amount_hesitations
    ]

    layer2_vector = [

        data.bene_dwell_ms,

        avg_amount_iki
    ]

    profile = db.query(
        database_models.UserProfile
    ).filter(
        database_models.UserProfile.user_id
        == data.user_id
    ).first()

    # Existing User
    if profile:

        pin_vectors = json.loads(
            profile.pin_vectors
        )

        layer1_vectors = json.loads(
            profile.layer1_vectors
        )

        layer2_vectors = json.loads(
            profile.layer2_vectors
        )

        if len(pin_vectors) < 5:

            pin_vectors.append(
                data.pin_vector
            )

            layer1_vectors.append(
                layer1_vector
            )

            layer2_vectors.append(
                layer2_vector
            )

            profile.pin_vectors = json.dumps(
                pin_vectors
            )

            profile.layer1_vectors = json.dumps(
                layer1_vectors
            )

            profile.layer2_vectors = json.dumps(
                layer2_vectors
            )

            db.commit()

            if len(pin_vectors) == 5:
                message = (
                    "Enrollment already complete"
            )
            
            message = (
                f"Sample {len(pin_vectors)}/5 stored"
            )

        else:

            message = (
                "Enrollment already complete"
            )

    # New User
    else:

        profile = database_models.UserProfile(

            user_id=data.user_id,

            pin_vectors=json.dumps(
                [data.pin_vector]
            ),

            layer1_vectors=json.dumps(
                [layer1_vector]
            ),

            layer2_vectors=json.dumps(
                [layer2_vector]
            )
        )

        db.add(profile)

        db.commit()

        message = "Sample 1/5 stored"

    db.close()

    return {
        "message": message
    }

#Verification Endpoint
@app.post("/verify")
def verify(
    data: VerificationRequest
):

    db = SessionLocal()

    profile = db.query(
        database_models.UserProfile
    ).filter(
        database_models.UserProfile.user_id
        == data.user_id
    ).first()

    if not profile:

        db.close()

        return {
            "error":
            "User not enrolled"
        }

    pin_vectors = json.loads(
        profile.pin_vectors
    )

    layer1_vectors = json.loads(
        profile.layer1_vectors
    )

    layer2_vectors = json.loads(
        profile.layer2_vectors
    )

    # Enrollment check
    if (
        len(pin_vectors) < 5
        or len(layer1_vectors) < 5
        or len(layer2_vectors) < 5
    ):

        db.close()

        return {
            "error":
            "Enrollment incomplete. Please complete 5 enrollment samples."
        }

    # Current Layer 2 feature
    avg_amount_iki = (
        sum(data.amount_iki)
        / len(data.amount_iki)
    )

    # --------------------
    # Layer 3 (DTW)
    # --------------------

    best_distance = float("inf")

    for vector in pin_vectors:

        distance = calculate_distance(
            vector,
            data.pin_vector
        )

        best_distance = min(
            best_distance,
            distance
        )

    print("DTW Distance:", best_distance)

    layer3_risk = get_layer3_risk(
        best_distance
    )

    # --------------------
    # Layer 1
    # --------------------

    layer1_risk = get_layer1_risk(

        training_data=layer1_vectors,

        decoy_tap_count=data.decoy_tap_count,

        amount_hesitations=data.amount_hesitations
    )

    # --------------------
    # Layer 2
    # --------------------

    layer2_risk = get_layer2_risk(

        training_data=layer2_vectors,

        bene_dwell_ms=data.bene_dwell_ms,

        amount_iki=data.amount_iki
    )

    # --------------------
    # Fusion
    # --------------------

    fusion = fusion_score(

        layer1_risk,

        layer2_risk,

        layer3_risk
    )

    composite = fusion[
        "composite_score"
    ]

    decision = fusion[
        "decision"
    ]

    # --------------------
    # Replay-attack defense
    # --------------------
    # A genuine session is never byte-identical twice. An exact duplicate of a
    # previously-seen package is a replay -> force BLOCK (and never learn from it).
    replay_detected = audit.is_replay(audit.payload_signature(data))
    if replay_detected:
        decision = "BLOCK"

    # --------------------
    # Adaptive Learning
    # --------------------

    if decision == "ALLOW":

        # ------------------
        # Layer 3 (DTW)
        # ------------------

        if len(pin_vectors) >= 20:

            pin_vectors.pop(0)

        pin_vectors.append(
            data.pin_vector
        )

        # ------------------
        # Layer 1
        # ------------------

        layer1_sample = [

            data.decoy_tap_count,

            data.amount_hesitations
        ]

        if len(layer1_vectors) < 20:

            # grow baseline until 20

            layer1_vectors.append(
                layer1_sample
            )

        else:

            # adaptive learning after 20

            layer1_vectors.pop(0)

            layer1_vectors.append(
                layer1_sample
            )

        # ------------------
        # Layer 2
        # ------------------

        layer2_sample = [

            data.bene_dwell_ms,

            avg_amount_iki
        ]

        if len(layer2_vectors) < 20:

            # grow baseline until 20

            layer2_vectors.append(
                layer2_sample
            )

        else:

            # adaptive learning after 20

            layer2_vectors.pop(0)

            layer2_vectors.append(
                layer2_sample
            )   

        profile.pin_vectors = json.dumps(
            pin_vectors
        )

        profile.layer1_vectors = json.dumps(
            layer1_vectors
        )

        profile.layer2_vectors = json.dumps(
            layer2_vectors
        )

    # --------------------
    # Session Log  (+ tamper-evident hash chain)
    # --------------------

    session_id = str(uuid4())[:8]
    timestamp = datetime.utcnow()

    last = (
        db.query(database_models.SessionLog)
        .order_by(database_models.SessionLog.id.desc())
        .first()
    )
    prev_hash = last.row_hash if (last and last.row_hash) else "GENESIS"

    this_hash = audit.row_hash(
        prev_hash, session_id, data.user_id,
        layer1_risk, layer2_risk, layer3_risk, composite, decision,
        timestamp.isoformat(),
    )

    log = database_models.SessionLog(

        session_id=session_id,

        timestamp=timestamp,

        user_id=data.user_id,

        layer1_score=layer1_risk,

        layer2_score=layer2_risk,

        layer3_score=layer3_risk,

        composite_score=composite,

        decision=decision,

        prev_hash=prev_hash,

        row_hash=this_hash,
    )

    db.add(log)

    db.commit()

    db.close()

    return {

        "layer1_score":
        layer1_risk,

        "layer2_score":
        layer2_risk,

        "layer3_score":
        layer3_risk,

        "composite_score":
        composite,

        "decision":
        decision,

        "replay_detected":
        replay_detected
    }


def _dev_risk(training_data, point):
    """Pure-deviation risk (no IsolationForest). Used when baseline < 10 samples."""
    dev = _normalized_deviation(point, training_data)
    return round(min(100.0, dev * 30.0), 1)


def _score_band(score: float) -> str:
    if score < 60:   return "green"
    elif score < 85: return "amber"
    else:            return "red"


def _get_or_create_profile(db, user_id: str):
    profile = db.query(database_models.UserProfile).filter(
        database_models.UserProfile.user_id == user_id
    ).first()
    if not profile:
        profile = database_models.UserProfile(
            user_id=user_id,
            pin_vectors="[]", layer1_vectors="[]", layer2_vectors="[]",
        )
        db.add(profile)
        db.flush()
    return profile


# ── Layer enrollment ────────────────────────────────────────────────────────

@app.post("/enroll/layer1")
def enroll_layer1(data: EnrollL1Request):
    db = SessionLocal()
    profile = _get_or_create_profile(db, data.user_id)
    baseline = json.loads(profile.l1_baseline or "[]")
    for ev in data.events:
        baseline.append([ev.decoy_interactions, ev.hover_hesitation_ms, ev.familiar_zone_latency_ms])
    profile.l1_baseline = json.dumps(baseline)
    db.commit()
    db.close()
    return {"message": f"{len(baseline)} L1 samples stored"}


@app.post("/enroll/layer2")
def enroll_layer2(data: EnrollL2Request):
    db = SessionLocal()
    profile = _get_or_create_profile(db, data.user_id)
    baseline = json.loads(profile.l2_baseline or "[]")
    for ev in data.events:
        baseline.append([ev.nav_entropy, ev.digit_fluency_gaps_ms, ev.beneficiary_dwell_ms])
    profile.l2_baseline = json.dumps(baseline)
    db.commit()
    db.close()
    return {"message": f"{len(baseline)} L2 samples stored"}


@app.post("/enroll/layer3")
def enroll_layer3(data: EnrollL3Request):
    db = SessionLocal()
    profile = _get_or_create_profile(db, data.user_id)
    baseline = json.loads(profile.l3_baseline or "[]")
    baseline.append(data.intervals)
    profile.l3_baseline = json.dumps(baseline)
    db.commit()
    db.close()
    return {"message": f"{len(baseline)} L3 samples stored"}


# ── Layer scoring ───────────────────────────────────────────────────────────

@app.post("/score/layer1")
def score_layer1(data: ScoreL1Request):
    db = SessionLocal()
    profile = db.query(database_models.UserProfile).filter(
        database_models.UserProfile.user_id == data.user_id
    ).first()
    db.close()
    baseline = json.loads(profile.l1_baseline or "[]") if profile else []
    if len(baseline) < 1:
        score = 0.0
    else:
        point = [data.decoy_interactions, data.hover_hesitation_ms, data.familiar_zone_latency_ms]
        fn = continuous_if_risk if len(baseline) >= 10 else _dev_risk
        score = fn(baseline, point)
    return {"score": score, "decision": _score_band(score)}


@app.post("/score/layer2")
def score_layer2(data: ScoreL2Request):
    db = SessionLocal()
    profile = db.query(database_models.UserProfile).filter(
        database_models.UserProfile.user_id == data.user_id
    ).first()
    db.close()
    baseline = json.loads(profile.l2_baseline or "[]") if profile else []
    if len(baseline) < 1:
        score = 0.0
    else:
        point = [data.nav_entropy, data.digit_fluency_gaps_ms, data.beneficiary_dwell_ms]
        fn = continuous_if_risk if len(baseline) >= 10 else _dev_risk
        score = fn(baseline, point)
    return {"score": score, "decision": _score_band(score)}


@app.post("/score/layer3")
def score_layer3(data: ScoreL3Request):
    db = SessionLocal()
    profile = db.query(database_models.UserProfile).filter(
        database_models.UserProfile.user_id == data.user_id
    ).first()
    db.close()
    baseline = json.loads(profile.l3_baseline or "[]") if profile else []
    if len(baseline) < 1:
        score = 0.0
    else:
        best_dist = min(calculate_distance(ref, data.intervals) for ref in baseline)
        score = get_layer3_risk(best_dist)
    return {"score": score, "decision": _score_band(score)}


# ── Composite fusion ────────────────────────────────────────────────────────

@app.post("/risk/composite")
def risk_composite(data: CompositeRequest):
    composite = round(0.3 * data.layer1_score + 0.4 * data.layer2_score + 0.3 * data.layer3_score, 1)
    decision = _score_band(composite)

    db = SessionLocal()
    session_id = str(uuid4())[:8]
    timestamp = datetime.utcnow()
    last = (
        db.query(database_models.SessionLog)
        .order_by(database_models.SessionLog.id.desc())
        .first()
    )
    prev_hash = last.row_hash if (last and last.row_hash) else "GENESIS"
    this_hash = audit.row_hash(
        prev_hash, session_id, data.user_id,
        data.layer1_score, data.layer2_score, data.layer3_score, composite, decision,
        timestamp.isoformat(),
    )
    db.add(database_models.SessionLog(
        session_id=session_id, timestamp=timestamp, user_id=data.user_id,
        layer1_score=data.layer1_score, layer2_score=data.layer2_score,
        layer3_score=data.layer3_score, composite_score=composite, decision=decision,
        prev_hash=prev_hash, row_hash=this_hash,
    ))
    db.commit()
    db.close()

    return {"composite_score": composite, "decision": decision}


@app.get("/maturity")
def maturity(user_id: str):
    """Baseline maturity / confidence for a user (cold-start indicator)."""
    db = SessionLocal()
    profile = (
        db.query(database_models.UserProfile)
        .filter(database_models.UserProfile.user_id == user_id)
        .first()
    )
    db.close()
    if not profile:
        return {"user_id": user_id, "samples": 0, "required": 5,
                "mature": False, "status": "unenrolled", "confidence": "none"}
    n = len(json.loads(profile.pin_vectors))
    return {
        "user_id": user_id,
        "samples": n,
        "required": 5,
        "mature": n >= 5,
        "status": "mature" if n >= 5 else "building",
        "confidence": "high" if n >= 5 else "low",
    }


@app.get("/audit/verify")
def audit_verify():
    """Walk the session_logs hash chain and report integrity."""
    db = SessionLocal()
    rows = (
        db.query(database_models.SessionLog)
        .order_by(database_models.SessionLog.id.asc())
        .all()
    )
    db.close()

    prev = "GENESIS"
    checked = 0
    for r in rows:
        if r.row_hash is None:
            continue  # legacy row written before the chain existed
        expected = audit.row_hash(
            prev, r.session_id, r.user_id,
            r.layer1_score, r.layer2_score, r.layer3_score,
            r.composite_score, r.decision, r.timestamp.isoformat(),
        )
        if expected != r.row_hash:
            return {"valid": False, "total": len(rows),
                    "verified": checked, "broken_at_session": r.session_id}
        prev = r.row_hash
        checked += 1

    return {"valid": True, "total": len(rows), "verified": checked, "broken_at_session": None}


@app.get("/logs")
def get_logs(user_id: Optional[str] = Query(default=None)):

    db = SessionLocal()

    q = db.query(database_models.SessionLog)
    if user_id:
        q = q.filter(database_models.SessionLog.user_id == user_id)
    logs = q.order_by(database_models.SessionLog.timestamp.desc()).limit(20).all()

    result = []

    for log in logs:

        result.append({

            "session_id":
            log.session_id,

            "timestamp":
            log.timestamp.isoformat(),

            "user_id":
            log.user_id,

            "layer1_score":
            log.layer1_score,

            "layer2_score":
            log.layer2_score,

            "layer3_score":
            log.layer3_score,

            "composite_score":
            log.composite_score,

            "decision":
            log.decision
        })

    db.close()

    return result