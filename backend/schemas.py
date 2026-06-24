from pydantic import BaseModel


class EnrollmentRequest(BaseModel):

    user_id: str

    decoy_tap_count: int

    amount_hesitations: int

    bene_dwell_ms: float

    amount_iki: list[float]

    pin_vector: list[float]


class VerificationRequest(BaseModel):

    user_id: str

    decoy_tap_count: int

    amount_hesitations: int

    bene_dwell_ms: float

    amount_iki: list[float]

    pin_vector: list[float]


# ── Layer-API schemas (separate signal space, used by /enroll/layerN + /score/layerN) ─

class L1Event(BaseModel):
    decoy_interactions: int
    hover_hesitation_ms: int
    familiar_zone_latency_ms: int

class EnrollL1Request(BaseModel):
    user_id: str
    events: list[L1Event]

class L2Event(BaseModel):
    nav_entropy: float
    digit_fluency_gaps_ms: int
    beneficiary_dwell_ms: int

class EnrollL2Request(BaseModel):
    user_id: str
    events: list[L2Event]

class EnrollL3Request(BaseModel):
    user_id: str
    intervals: list[int]

class ScoreL1Request(BaseModel):
    user_id: str
    decoy_interactions: int
    hover_hesitation_ms: int
    familiar_zone_latency_ms: int

class ScoreL2Request(BaseModel):
    user_id: str
    nav_entropy: float
    digit_fluency_gaps_ms: int
    beneficiary_dwell_ms: int

class ScoreL3Request(BaseModel):
    user_id: str
    intervals: list[int]

class CompositeRequest(BaseModel):
    user_id: str
    layer1_score: float
    layer2_score: float
    layer3_score: float