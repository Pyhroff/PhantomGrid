# PhantomGrid — Technical Documentation
**CBI Hackathon 2026 | Team ZeroIntent (S.No. 8) | IIIT Kottayam**

---

## 1. Problem Statement

Account Takeover (ATO) fraud in Public Sector Banks (PSBs) has reached a critical inflection point. In FY2023, Indian PSBs reported over ₹7,400 crore in digital fraud losses — the majority occurring **after successful login**. Attackers today do not break authentication systems; they bypass them entirely using stolen credentials purchased from dark-web marketplaces.

The fundamental failure of current authentication is **temporal**: systems verify identity once at the login gate, then trust the session unconditionally for its duration. An attacker who presents valid credentials — obtained through phishing, SIM swap, social engineering, or data breaches — is indistinguishable from the legitimate user by any existing control.

Password complexity mandates, OTP requirements, and device fingerprinting each address one attack vector in isolation. None of them answer the core question that matters at the point of a ₹5 lakh fund transfer: **Is the person currently operating this session the enrolled account holder?**

PhantomGrid answers that question — continuously, silently, and without adding any friction to the 99.9% of sessions that are legitimate.

---

## 2. Proposed Solution

PhantomGrid is a **three-layer passive behavioural authentication engine** that runs transparently beneath a banking portal. Rather than challenging users with additional factors, it observes the natural behavioural signatures that emerge from how users interact with the interface — patterns that are unconscious, stable over time, and practically impossible to replicate without direct observation of the specific individual.

The system operates in two phases:

**Enrollment (Sessions 1–5):** During the user's first five transactions, PhantomGrid silently collects behavioural baseline vectors across three independent signal domains. No user action is required; the system learns from normal usage.

**Continuous Scoring (Session 6+):** Every subsequent transaction is scored against the enrolled baseline in real time. A composite risk score (0–100) determines the response: allow the transaction, trigger silent step-up OTP re-authentication, or block the session outright.

The analyst dashboard provides real-time visibility into every session score, per-layer risk breakdown, explainability reasoning, and a tamper-evident audit trail — giving compliance officers and fraud analysts the tools they need without requiring access to individual transaction data.

---

## 3. System Architecture

PhantomGrid follows a three-tier architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│  TIER 1: Signal Capture — Madapati Jyoti Radithya   │
│  capture.js — behavioural hooks injected into       │
│  the banking portal. Captures L1/L2/L3 signals      │
│  and packages them into a single JSON payload.      │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP POST (JSON)
┌─────────────────────▼───────────────────────────────┐
│  TIER 2: ML Inference Engine (FastAPI + Python)     │
│  • Isolation Forest per-user models (L1, L2)        │
│  • Dynamic Time Warping comparator (L3)             │
│  • Continuous scoring engine (services/scoring.py)  │
│  • Fusion layer (L1×0.30 + L2×0.40 + L3×0.30)      │
│  • Replay defence (SHA-256 signature window)        │
│  • Adaptive baseline updater                        │
│  • Tamper-evident session logger                    │
└─────────────────────┬───────────────────────────────┘
                      │ SQLite (local)
┌─────────────────────▼───────────────────────────────┐
│  TIER 3: Analyst Dashboard (Vanilla JS)             │
│  • Polls GET /logs every 2 seconds                  │
│  • Live risk gauge + per-layer breakdown            │
│  • WHY THIS DECISION explainability panel           │
│  • BLOCK alert overlay + audio cue                  │
│  • Audit chain integrity badge                      │
│  • Baseline maturity indicator                      │
└─────────────────────────────────────────────────────┘
```

### Trust Boundary Model

The system defines four trust boundaries: Browser ↔ API, API ↔ Database, External Admin ↔ Database, and Dashboard ↔ API. All inter-boundary traffic is validated. Behavioral payloads crossing the Browser ↔ API boundary are signature-checked (replay defence) and schema-validated (Pydantic 422 enforcement) before any ML inference runs.

---

## 4. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| API Framework | FastAPI (Python 3.12) | Async, auto-validates with Pydantic, generates Swagger docs |
| ASGI Server | Uvicorn | Production-grade ASGI server, minimal overhead |
| ML — Anomaly Detection | scikit-learn IsolationForest | Unsupervised — no fraud labels required at enrollment |
| ML — Rhythm Comparison | dtaidistance (DTW) | Handles natural speed variation in keystroke sequences |
| Database ORM | SQLAlchemy 2.0 | Declarative models, migration-compatible |
| Database | SQLite | Zero-config for PoC; schema is PostgreSQL-compatible |
| Request Validation | Pydantic v2 | Zero-overhead schema enforcement at API boundary |
| Audit Cryptography | Python `hashlib` (SHA-256) | SHA-256 hash chain + payload signatures |
| Frontend | Vanilla HTML/CSS/JS | No build step — fully portable, zero dependency |
| Dashboard Polling | `setInterval` + `fetch` | 2-second REST polling (WebSocket in production roadmap) |
| Test Framework | pytest + requests | Integration tests against live backend |
| Benchmarking | matplotlib + numpy | ROC curve, confusion matrix, AUC computation |

---

## 5. Workflow

### 5.1 Enrollment Flow

```
User initiates payment
       ↓
capture.js collects signals during transaction
  └─ decoy_tap_count, amount_hesitations (L1)
  └─ bene_dwell_ms, amount_iki[] (L2)
  └─ pin_vector[] (L3 — inter-key intervals only, no digits)
       ↓
POST /enroll {user_id, all signals}
       ↓
Backend extracts feature vectors:
  L1: [decoy_tap_count, amount_hesitations]
  L2: [bene_dwell_ms, avg(amount_iki)]
  L3: pin_vector (raw)
       ↓
Appended to user_profiles JSON blobs
       ↓
After 5 samples: enrollment complete
capture.js switches to VERIFY mode automatically
```

### 5.2 Scoring Flow

```
User initiates payment (session 6+)
       ↓
capture.js packages signals → POST /verify
       ↓
Replay check: SHA-256(payload) in seen_signatures within 5min?
  YES → forced BLOCK, replay_detected: true
  NO  → continue
       ↓
Layer scoring (parallel):
  L1: continuous_if_risk(baseline, [decoy_taps, hesitations])
  L2: continuous_if_risk(baseline, [bene_dwell, avg_iki])
  L3: dtw_to_risk(min DTW distance to any enrolled PIN vector)
       ↓
Fusion: composite = L1×0.30 + L2×0.40 + L3×0.30
       ↓
Decision: ALLOW (<60) | OTP (60–79) | BLOCK (≥80)
       ↓
If ALLOW: append session to baseline (adaptive learning, window 20)
       ↓
Compute hash chain: row_hash = SHA256(prev_hash|session_data)
Write to session_logs
       ↓
Return {layer1_score, layer2_score, layer3_score, composite_score,
        decision, replay_detected}
       ↓
Dashboard polls GET /logs every 2s → updates live
```

---

## 6. Database Design

### Table: `user_profiles`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `user_id` | TEXT UNIQUE | User identifier |
| `layer1_vectors` | TEXT (JSON) | List of [decoy_tap_count, amount_hesitations] pairs |
| `layer2_vectors` | TEXT (JSON) | List of [bene_dwell_ms, avg_amount_iki] pairs |
| `pin_vectors` | TEXT (JSON) | List of PIN inter-key interval vectors |

Vectors are stored as JSON blobs. The IsolationForest is **not serialised** — it is fit on-the-fly from the raw vectors at each `/verify` call. This keeps the schema simple and ensures the model always reflects the latest baseline including adaptive updates.

### Table: `session_logs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `session_id` | TEXT UNIQUE | UUID-derived 8-char identifier |
| `timestamp` | DATETIME | UTC timestamp of session |
| `user_id` | TEXT | User who initiated session |
| `layer1_score` | REAL | L1 risk score (0–100) |
| `layer2_score` | REAL | L2 risk score (0–100) |
| `layer3_score` | REAL | L3 risk score (0–100) |
| `composite_score` | REAL | Fused risk score (0–100) |
| `decision` | TEXT | ALLOW \| OTP \| BLOCK |
| `row_hash` | TEXT | SHA-256 of this row's content |
| `prev_hash` | TEXT | SHA-256 of the preceding row (chain link) |

The `row_hash`/`prev_hash` pair forms a cryptographic hash chain. Any retrospective modification of any row breaks the chain at exactly that point, which is detectable via `GET /audit/verify`.

---

## 7. AI / ML Models

### 7.1 Isolation Forest (Layers 1 & 2)

**Algorithm:** Isolation Forest (Liu et al., 2008)

Isolation Forest is an unsupervised anomaly detection algorithm that exploits the property that anomalies are rare and different. It builds an ensemble of 100 isolation trees by recursively partitioning the feature space with random splits. Normal points — surrounded by similar samples — require many splits to isolate (deep paths). Anomalies require few (shallow paths).

**PhantomGrid implementation:** Standard IF is unreliable on the small (5-sample) per-user baselines typical at enrollment. We solve this with a hybrid engine in `services/scoring.py`:

- **Gate:** IF `decision_function` classifies the session as inlier (normal) or outlier (anomaly).
- **Magnitude:** `_normalized_deviation()` computes the Euclidean distance from the baseline centroid in normalised standard-deviation units, flooring each feature's std to prevent degenerate near-zero spreads.
- **Composite score:** Inliers score 0–45 (mild deviation is expected); outliers score 55–100 proportional to deviation magnitude.
- **Small-baseline fallback:** For baselines < 10 samples, IF is skipped entirely and pure deviation scoring is used (monotonic, deterministic, always correct).

```python
def continuous_if_risk(training_data, point):
    deviation = _normalized_deviation(point, training_data)
    if len(training_data) < 10:
        return round(min(100.0, deviation * 30.0), 1)
    model = IsolationForest(contamination=0.1, random_state=42).fit(training_data)
    gate = model.decision_function([point])[0]
    if gate >= 0:
        return round(min(45.0, deviation * 22.0), 1)
    return round(min(100.0, 55.0 + deviation * 12.0), 1)
```

**Hyperparameters:** `contamination=0.1` (10% noise tolerance), `n_estimators=100`, `random_state=42`.

### 7.2 Dynamic Time Warping (Layer 3)

**Algorithm:** DTW (Sakoe & Chiba, 1978) via `dtaidistance`

Euclidean distance fails for keystroke sequences because natural speed variation (typing 10% faster when stressed) produces large distances even for the same individual. DTW finds the optimal elastic alignment between two sequences before measuring residual distance.

**PhantomGrid implementation:** For each `/verify` call, DTW distance is computed between the query PIN vector and every enrolled baseline vector. The minimum distance is taken (best-match strategy, reduces FRR from natural variation). Distance is mapped to 0–100 via `min(100, dist/180 × 100)` — a calibrated linear mapping where 180ms total deviation saturates to full risk.

```python
def dtw_to_risk(distance):
    return round(min(100.0, (distance / 180.0) * 100.0), 1)
```

### 7.3 Adaptive Learning

After every ALLOW decision, the current session's behavioural vectors are appended to the user's baseline (sliding window, capped at 20 samples per layer). This implements a form of online incremental learning — the model drifts toward the user's current behaviour without explicit retraining, handling natural behavioural evolution over time.

---

## 8. APIs and External Services

PhantomGrid uses no external APIs or cloud services. All computation is local.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/enroll` | POST | Store one enrollment sample |
| `/verify` | POST | Score session → {scores, decision, replay_detected} |
| `/logs` | GET | Last 10 session log rows |
| `/maturity` | GET | Baseline maturity for user |
| `/audit/verify` | GET | Hash chain integrity check |

No third-party ML APIs, no cloud inference services, no external data providers. The only network dependency is the browser calling the local FastAPI server.

---

## 9. Security Measures

### 9.1 Replay-Attack Defence
SHA-256 signature computed over the full behavioral payload. Exact duplicates within a 5-minute window are blocked (`services/audit.py::is_replay()`). Prevents credential-stuffing-style attacks where a captured valid session payload is retransmitted.

### 9.2 Tamper-Evident Audit Chain
SHA-256 hash chain over `session_logs`. `row_hash = SHA256(prev_hash | session_id | user_id | scores | decision | timestamp)`. Modification of any record is detectable within a single `GET /audit/verify` call. Satisfies RBI Master Circular requirements for immutable transaction audit trails.

### 9.3 Input Validation
All API requests are validated via Pydantic v2 schemas before any ML code executes. Malformed or incomplete payloads receive HTTP 422. No SQL injection surface (SQLAlchemy ORM with parameterised queries).

### 9.4 PII Minimisation
PIN digits are never persisted. Only inter-keystroke intervals (millisecond timing gaps between digit entries) are stored. These values cannot be reverse-engineered to recover the PIN. No account numbers, names, or transaction amounts are stored by PhantomGrid.

### 9.5 CORS Policy
`allow_origins=["*"]` for PoC portability. Production hardening: restrict to bank's origin domain.

### 9.6 STRIDE Threat Coverage

| Threat | Control |
|--------|---------|
| Spoofing | Per-user IF models — impersonation requires behavioral mimicry |
| Tampering | Hash chain audit trail — any DB edit is detectable |
| Repudiation | Immutable session_logs with timestamps |
| Information Disclosure | No PII stored; CORS restricted in production |
| Denial of Service | Rate-limiting + lightweight inference (<5ms) |
| Elevation of Privilege | /enroll requires authenticated session in production |

---

## 10. Scalability Considerations

| Concern | PoC Approach | Production Path |
|---------|-------------|-----------------|
| Database | SQLite (single file) | PostgreSQL (drop-in connection string swap) |
| Model storage | Fit on-the-fly | Pre-serialised per-user IF models (joblib) + Redis cache |
| Dashboard updates | REST polling (2s) | WebSocket streaming (50ms) |
| Deployment | Single machine | Docker + AWS ap-south-1 (data localisation) |
| Baseline training | 5 samples | Shadow mode with 30+ samples before enforcement |
| Multi-region | N/A | RBI localisation: all data in Indian cloud regions |

Inference time per session: L1 ~0.1ms, L2 ~0.1ms, L3 ~0.01ms, fusion ~0.001ms. Total < 5ms. Does not block the payment flow.

---

## 11. Assumptions and Limitations

**Assumptions:**
- Users enroll on the same device they will use for live transactions (PIN rhythm is device-specific — keyboard type affects timings)
- At least 5 enrollment samples are available before enforcement begins
- The `/enroll` endpoint is called within an authenticated session (prevents enrollment poisoning — flagged in threat model as production requirement)
- `capture.js` has not been tampered with by a sophisticated client-side attacker (XSS vector)

**Limitations:**
- **Cold start:** Under 5 enrollment samples, model reliability is reduced. Maturity endpoint signals this explicitly
- **Cross-device degradation:** PIN rhythm changes significantly across physical keyboards. Mitigation: per-device baseline profiles
- **Sustained adaptive poisoning:** A sophisticated attacker achieving repeated OTP decisions over many sessions could gradually drift the baseline. Mitigation: exponential moving average with drift detection (production roadmap)
- **SQLite concurrency:** Single-writer limitation. Not suitable for high-concurrency production without migration to PostgreSQL

---

## 12. Future Enhancements

| Feature | Description | Priority |
|---------|-------------|----------|
| **Mouse/touch dynamics** | Add L4 layer capturing scroll velocity, touch pressure (mobile), pointer trajectory entropy | High |
| **Device-aware profiles** | Separate baseline per device fingerprint — eliminates cross-device FRR spike | High |
| **Federated baseline** | Train a global population model on aggregate (anonymised) behavioural data to bootstrap cold-start users | Medium |
| **WebSocket streaming** | Real-time dashboard updates at 50ms (vs 2s polling) | Medium |
| **PostgreSQL migration** | Drop-in connection string change; enables horizontal scaling | High |
| **Drift detection** | Statistical test on baseline evolution — alert if baseline shifts faster than natural behavioural drift | Medium |
| **Mobile SDK** | Capture touch pressure, swipe velocity, accelerometer during PIN entry — richer L3 signal for mobile banking | High |
| **Active deception layer** | Randomise decoy positions per session — hardens against attackers who learn the layout over time | Low |
| **Regulatory dashboard** | RBI-ready reporting module: per-user risk history, aggregate fraud metrics, audit export | Medium |

---

---

## Team

| Role | Name |
|------|------|
| Frontend — Signal Capture | Madapati Jyoti Radithya |
| Backend — ML Engine | Kontheti Sai Akhilesh |
| Dashboard + Security + Tests (Lead) | Praising Y Harris Ratnam |

*PhantomGrid — Passive. Invisible. Unbeatable.*
*Team ZeroIntent | S.No. 8 | CBI Hackathon 2026 | MNNIT Allahabad | IIIT Kottayam*
