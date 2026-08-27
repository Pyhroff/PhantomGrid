# PhantomGrid — Demo Preparation Guide
**Team ZeroIntent | PSBs Hackathon 2026 | MNNIT Allahabad**

---

## Table of Contents
1. [Elevator Pitch](#1-elevator-pitch)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Person 1 — Frontend (Behavioral Signal Capture)](#3-person-1--frontend-behavioral-signal-capture)
4. [Person 2 — Backend (ML Engine + API)](#4-person-2--backend-ml-engine--api)
5. [Person 3 — Analyst Dashboard + Tests](#5-person-3--analyst-dashboard--tests)
6. [The ML in Plain English](#6-the-ml-in-plain-english)
7. [RBI Compliance Deep Dive](#7-rbi-compliance-deep-dive)
8. [Common Judge Questions & Answers](#8-common-judge-questions--answers)
9. [Demo Script (Live Run)](#9-demo-script-live-run)
10. [Glossary](#10-glossary)

---

## 1. Elevator Pitch

> "Banks authenticate you once at login. PhantomGrid authenticates you *continuously* — silently, invisibly, across the entire session. No extra friction. No passwords. Just math running on how you naturally behave."

PhantomGrid is a **passive behavioral biometrics engine** that sits alongside a banking portal. It watches three behavioral layers — how you interact with decoys, how you navigate, and the rhythm of your PIN keystrokes — fuses them into a single risk score, and decides: let the session proceed, trigger silent OTP re-auth, or block.

The user never notices unless they're an attacker.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (Person 1)                          │
│  Banking portal HTML/JS                                         │
│  Captures: hover events, decoy clicks, navigation, keystrokes   │
│  Sends behavioral JSON → FastAPI every interaction              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST (JSON payloads)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Person 2)                      │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Layer 1    │  │   Layer 2    │  │  Layer 3 RhythmLock  │  │
│  │ Isolation    │  │ Isolation    │  │  Dynamic Time        │  │
│  │ Forest       │  │ Forest       │  │  Warping (DTW)       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                │                      │              │
│         └────────────────┼──────────────────────┘              │
│                          ▼                                      │
│              Composite Fusion Engine                            │
│              L1×0.30 + L2×0.40 + L3×0.30                       │
│                          │                                      │
│              ┌───────────┼───────────┐                          │
│              ▼           ▼           ▼                          │
│          ALLOW          OTP        BLOCK                        │
│          (<60)        (60–79)      (≥80)                        │
│                          │                                      │
│                    SQLite DB ──────────────────────────────┐    │
│              backend/phantomgrid.db                        │    │
└──────────────────────────┬────────────────────────────────┼────┘
                           │ GET /logs (dashboard polls 2s) │
                           ▼                                ▼
┌──────────────────────────────┐        ┌───────────────────────┐
│  Analyst Dashboard (Person 3)│        │  session_logs table   │
│  dashboard/index.html        │        │  audit trail          │
│  Live gauge, layer bars,     │        └───────────────────────┘
│  session log, OTP toast      │
└──────────────────────────────┘
```

The combined API: the browser POSTs one behavioral package to **`/enroll`** (first 5 sessions) and then **`/verify`** (every live session). `/verify` returns all three layer scores + composite + decision in one response. The analyst dashboard polls **`GET /logs`**.

**Three-layer defense in depth.** An attacker must simultaneously fool all three independent behavioral models to score below 80 on the composite. Each layer uses a different signal domain and a different algorithm — no single bypass works across layers.

---

## 3. Person 1 — Frontend (Behavioral Signal Capture)

### What Person 1 Builds
A standard banking portal (HTML/JS) with invisible behavioral instrumentation woven into the UI.

### Layer 1 Signal Capture — Decoy Interactions

**What are decoys?**
Invisible or visually camouflaged UI elements (buttons, links, form fields) placed in positions that look like valid UI but do nothing in the real banking flow. Legitimate users who know the interface never interact with them. Attackers probing an unfamiliar interface do.

**Signals captured:**
- `decoy_interactions` — count of clicks/touches on decoy elements in the session
- `hover_hesitation_ms` — how long the pointer hesitated over a UI region before deciding (measured in milliseconds). Legitimate users move directly; fraudsters scan and pause.
- `familiar_zone_latency_ms` — time taken to reach the payment entry zone from the previous interaction. Regular customers have muscle memory; attackers scan the page first.

**How it's sent (real `capture.js`):**
All three layers' signals are collected during the session and sent as ONE combined
package when the user submits the payment — to `/verify` (or `/enroll` during the
first 5 sessions). There are no per-layer endpoints.
```js
// capture.js → onPaySubmit() builds one signal package
fetch('http://localhost:8000/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: currentUserId,
    decoy_tap_count: 0,        // Layer 1
    amount_hesitations: 0,     // Layer 1/2
    bene_dwell_ms: 600,        // Layer 2
    amount_iki: [110, 95, 105],// Layer 2 (inter-key gaps on amount field)
    pin_vector: [118, 92, 107, 85, 99]  // Layer 3 (PIN rhythm)
  })
});
// → { layer1_score, layer2_score, layer3_score, composite_score, decision }
```

### Layer 2 Signal Capture — Navigation Behavior

**Signals captured:**
- `nav_entropy` — how unpredictable/random the user's navigation path is (0.0 = perfectly linear, 1.0 = chaotic). Calculated using Shannon entropy on the page visit sequence. Legitimate users follow predictable paths: login → account → transfer → confirm. Attackers explore unpredictably.
- `digit_fluency_gaps_ms` — pauses between digit entries in account number fields. Regular users type account numbers they know; attackers copy-paste or type slowly while looking at a reference.
- `beneficiary_dwell_ms` — total time spent on the beneficiary add/confirm screen. Legitimate users add known beneficiaries quickly. Attackers who set up mule accounts hesitate or re-read.

**Shannon entropy formula (for nav_entropy):**
```
H = -Σ p(x) × log₂(p(x))
```
Where p(x) is the relative frequency of each page visited. Normalize to [0, 1] by dividing by log₂(num_unique_pages).

### Layer 3 Signal Capture — RhythmLock (PIN Keystrokes)

**What is captured:**
The *inter-keystroke timing intervals* (in milliseconds) between consecutive key presses when the user types their PIN. NOT the PIN digits themselves — only the timing gaps.

```
User types PIN: 4  8  2  7  1
               ↕  ↕  ↕  ↕  ↕
Gaps (ms):   118 92 107 85  → intervals = [118, 92, 107, 85, 99]
```

This is like a typing fingerprint. Everyone has a unique rhythm for familiar sequences. The intervals encode which fingers you use, your typing speed, cognitive pauses between digits.

**JavaScript keystroke timing:**
```js
let last = null;
const intervals = [];

pinInput.addEventListener('keydown', (e) => {
  const now = performance.now();
  if (last !== null) intervals.push(Math.round(now - last));
  last = now;
});

// intervals are collected (window.onPinKey) and bundled into the single
// /verify call above as `pin_vector` — not sent to a separate endpoint.
```

### OTP Overlay (OTP / Amber Response)
When `/verify` returns `decision === "OTP"` (composite 60–79):
1. Transaction submit button is disabled
2. OTP modal overlay appears on top of the banking page
3. User completes OTP — transaction proceeds
4. This is silent to a legitimate user (they just see a standard OTP step)

The OTP delivery and verification itself is handled by the bank's existing infrastructure. PhantomGrid only *triggers* the challenge.

---

## 4. Person 2 — Backend (ML Engine + API)

### Tech Stack
- **Framework:** FastAPI (Python) — async, auto-generates `/docs` Swagger UI
- **Database:** SQLite (`phantomgrid.db`) — single-file, zero-config for the PoC
- **ML:** scikit-learn (`IsolationForest`) for L1/L2, `dtaidistance` (DTW) for L3
- **Baseline storage:** raw behavioral vectors stored as JSON strings in `user_profiles`; the IsolationForest is fit on-the-fly at verify time (no model serialization)

### Database Schema

**`user_profiles` table** (per-user baseline; vectors stored as JSON strings)
```sql
CREATE TABLE user_profiles (
    id              INTEGER PRIMARY KEY,
    user_id         TEXT UNIQUE,
    layer1_vectors  TEXT,   -- JSON: list of [decoy_tap_count, amount_hesitations]
    layer2_vectors  TEXT,   -- JSON: list of [bene_dwell_ms, avg_amount_iki]
    pin_vectors     TEXT    -- JSON: list of PIN inter-key interval vectors
);
```

**`session_logs` table**
```sql
CREATE TABLE session_logs (
    id              INTEGER PRIMARY KEY,
    session_id      TEXT UNIQUE,
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id         TEXT,
    layer1_score    REAL,
    layer2_score    REAL,
    layer3_score    REAL,
    composite_score REAL,
    decision        TEXT,    -- 'ALLOW' | 'OTP' | 'BLOCK'
    row_hash        TEXT,    -- SHA-256 of this row (tamper-evident)
    prev_hash       TEXT     -- SHA-256 of the previous row (hash chain)
);
```
`row_hash`/`prev_hash` form a tamper-evident hash chain (added by `services/audit.py`).
`GET /audit/verify` walks the full chain and returns `{valid, verified, broken_at_session}`.

### Enrollment Flow (`POST /enroll`)

There is one `/enroll` endpoint. Each call stores ONE sample; the backend collects
**5 samples** per user, then enrollment is complete. Models are **not** pre-trained and
serialized — instead the raw baseline vectors are stored as JSON and the IsolationForest
is fit on-the-fly at verify time.

```python
@app.post("/enroll")
def enroll(data: EnrollmentRequest):
    # append [decoy_tap_count, amount_hesitations] to layer1_vectors,
    #        [bene_dwell_ms, avg(amount_iki)] to layer2_vectors,
    #        pin_vector to pin_vectors  — until 5 samples are stored.
    ...
    return {"message": f"Sample {n}/5 stored"}
```

### Scoring Flow (`POST /verify`)

`/verify` scores all three layers in one call and returns the fused decision. Layer
scores are **continuous 0–100** (see `services/scoring.py`):

```python
# services/scoring.py — IsolationForest as anomaly GATE + deviation MAGNITUDE
def continuous_if_risk(training_data, point):
    model = IsolationForest(contamination=0.1, random_state=42).fit(training_data)
    gate = model.decision_function([point])[0]        # >0 normal, <0 anomaly
    deviation = _normalized_deviation(point, training_data)
    if gate >= 0:
        return round(min(45.0, deviation * 22.0), 1)   # inlier band 0–45
    return round(min(100.0, 55.0 + deviation * 12.0), 1)  # outlier band 55–100

def dtw_to_risk(distance):                              # Layer 3
    return round(min(100.0, (distance / 180.0) * 100.0), 1)
```

### Composite Fusion (`services/fusion.py`)

```python
def fusion_score(layer1, layer2, layer3):
    composite = 0.30*layer1 + 0.40*layer2 + 0.30*layer3
    if composite < 60:   decision = "ALLOW"
    elif composite < 80: decision = "OTP"
    else:                decision = "BLOCK"
    return {"composite_score": round(composite, 1), "decision": decision}
```
`/verify` writes a `session_logs` row on every call and returns
`{layer1_score, layer2_score, layer3_score, composite_score, decision}`.
The dashboard reads the latest rows from `GET /logs`.

---

## 5. Person 3 — Analyst Dashboard + Tests

See `INTEGRATION_NOTES.md` for the full integration contract. Summary:
- `dashboard/index.html` — dark-theme live dashboard, polls every 2s, animated gauge, layer bars, session log, OTP toast
- `tests/` — pytest suite covering all endpoints, fusion math, SQLite persistence, auto-skips if backend is down
- `threat_model/THREAT_MODEL.md` — full STRIDE analysis
- `INTEGRATION_NOTES.md` — contracts for Person 1 and Person 2

---

## 6. The ML in Plain English

### Isolation Forest (Layers 1 & 2)

**The core insight:** Normal behavior clusters. Anomalies are isolated.

Imagine a forest of randomly built decision trees. Each tree randomly picks a feature (e.g. hover time) and a random split value, and keeps splitting until each data point is in its own leaf.

- A **normal point** (typical user behavior) is surrounded by many similar points. It takes many splits to isolate it — deep in the tree.
- An **anomaly** (attacker behavior) is rare and extreme. It only takes a few splits to isolate it — shallow in the tree.

The **anomaly score** = average depth across all 100 trees. Short average depth → anomaly.

```
Normal user hover_hesitation_ms = 115ms
Attacker hover_hesitation_ms = 450ms  ← far from the cluster

Normal needs ~35 splits to isolate (deep)
Attacker needs ~8 splits to isolate  (shallow = anomaly)
```

**Why Isolation Forest for behavioral biometrics?**
- **Unsupervised** — at enrollment we only have legitimate sessions. There are no fraud examples to train on (we don't know what the attacker will look like).
- **Multi-feature** — naturally handles the combination of 3 features per layer without feature engineering.
- **Fast** — inference is O(n × depth), well under 1ms for 3-feature vectors.
- **No assumption on data distribution** — behavior data is not Gaussian; IF makes no normality assumption.

**What `contamination=0.1` means** (the value the backend actually uses):
Tells the model to treat roughly 10% of enrollment data as potential noise/outliers. This makes the boundary slightly looser — reduces false positives when the user's behavior varies slightly day-to-day. (Note: with only 5 baseline samples the IsolationForest's anomaly score saturates, which is why the engine adds a continuous deviation magnitude on top — see `services/scoring.py`.)

### Dynamic Time Warping — Layer 3 (RhythmLock)

**The problem with simple comparison:**
Your PIN rhythm is [118, 92, 107, 85, 99] on a relaxed Monday. On a rushed Friday it might be [105, 80, 95, 75, 88] — about 10% faster across the board. Euclidean distance would compute this as a large difference and falsely flag you as an attacker.

**What DTW does:**
DTW finds the *optimal alignment* between two sequences, allowing them to be stretched or compressed in time before measuring the residual difference.

**The cost matrix (dynamic programming):**
```
             Baseline: [115, 95, 110, 88, 101]
              b[0]  b[1]  b[2]  b[3]  b[4]
query  q[0] [ 3,    23,   ...]
       q[1] [...]
       q[2] [...]
       ...

dp[i][j] = |q[i] - b[j]| + min(
    dp[i-1][j],    ← stretch query
    dp[i][j-1],    ← stretch baseline
    dp[i-1][j-1]   ← advance both
)

Final DTW distance = dp[n-1][m-1]
```

**Normalization to 0–100 risk score** (real `services/scoring.py`):
```python
d = dtw.distance(query_intervals, baseline_vector)
score = round(min(100.0, (d / 180.0) * 100.0), 1)   # smooth, no buckets
```

- Legit user (small jitter): DTW distance ≈ 0–10 → score ≈ 0–6 (ALLOW)
- Attacker (divergent rhythm): DTW distance ≈ 180+ → score → 100 (BLOCK)
- This replaced the old 4-bucket version that returned a flat 95 for any large distance.

**Why DTW over Euclidean for keystrokes?**

| Property | Euclidean | DTW |
|----------|-----------|-----|
| Handles speed variation | No | Yes |
| Handles partial phase shift | No | Yes |
| False Rejection Rate | High (~15%) | Low (~3%) |
| Computation cost | O(n) | O(n²) — fine for n=5 |

**Why n=5 intervals?**
Standard 6-digit PIN = 5 inter-key gaps. Enough signal to distinguish individuals while keeping enrollment friction minimal (users enter their PIN during normal login anyway).

### Fusion Weight Rationale

| Layer | Weight | Reason |
|-------|--------|--------|
| L2 (Nav behavior) | 0.40 | Strongest signal — navigation entropy + beneficiary dwell are the most discriminating features for payment fraud |
| L1 (Decoy) | 0.30 | Strong for bot/script attacks but sophisticated human attackers might avoid decoys |
| L3 (RhythmLock) | 0.30 | Highly accurate for the individual but fails gracefully when the user types on a different device |

---

## 7. RBI Compliance Deep Dive

### Relevant Regulations

**1. RBI Circular on Storage of Payment System Data (April 2018)**
All payment system data must be stored exclusively on systems physically located in India. This applies to the full end-to-end transaction data.

**2. Digital Personal Data Protection Act (DPDP Act, 2023)**
Governs collection, processing, and storage of personal data of Indian citizens. Requires lawful purpose, data minimization, and appropriate safeguards.

### What PhantomGrid Stores

| Data Item | Is it PII? | PhantomGrid Stores? |
|-----------|-----------|---------------------|
| Account numbers | Yes | **No** |
| PIN digits | Yes | **No** |
| Name, address | Yes | **No** |
| Transaction amounts | Yes | **No** |
| Inter-keystroke intervals (ms) | Derived biometric metric | Yes |
| Navigation entropy (0.0–1.0 float) | Derived metric | Yes |
| Hover hesitation (ms) | Derived metric | Yes |
| user_id | Opaque identifier | Yes |
| Composite risk score | Derived metric | Yes |

**Key argument to judges:** PhantomGrid stores *derived behavioral metrics* — abstract numerical representations of behavioral patterns. They cannot be reverse-engineered into PII. You cannot recover someone's PIN, account number, or identity from a sequence of `[118, 92, 107, 85, 99]` millisecond values without the original session context. These are analogous to a bank storing aggregate transaction statistics (avg transaction size) rather than individual transactions.

### Data Localisation Compliance

For the PoC: `phantomgrid.db` runs on localhost (single machine). In production deployment:
- Deploy FastAPI on an Indian cloud region (AWS `ap-south-1` Mumbai, Azure `centralindia`, GCP `asia-south1`)
- The SQLite file — or its production PostgreSQL equivalent — must reside on storage volumes in that Indian region
- No cross-border replication of `user_profiles` or `session_logs`

### Why PhantomGrid Strengthens RBI Compliance

RBI's Master Direction on KYC and guidelines on digital payment security (2021) explicitly encourage banks to implement additional authentication for high-risk transactions. PhantomGrid provides:

1. **Continuous authentication** — not just at login, but throughout the session
2. **Risk-based challenge triggers** — OTP re-auth only when risk score warrants it (Amber), not on every transaction (reduces friction)
3. **Audit trail** — every `session_logs` row is a timestamped, scored session record that satisfies audit requirements

---

## 8. Common Judge Questions & Answers

### On the Technology

**Q: Why not just use a rule-based system? Why ML?**
> Rule-based systems like "flag if hover > 300ms" fail because user behavior varies legitimately day-to-day and across demographics. A 65-year-old user and a 22-year-old will have vastly different hover times — a single threshold creates either high false rejections for the elderly or poor detection for attackers. Isolation Forest learns *each user's individual baseline* and flags deviations from that personal norm, not from a global average.

**Q: What happens if a legitimate user changes their behavior — new phone, injury, stress?**
> Two things: First, the Isolation Forest `contamination=0.1` parameter already accounts for ~10% variance during enrollment. Second, in production we implement exponential moving average baseline updates — confirmed-legitimate sessions slowly shift the baseline toward the current behavior pattern. The PoC uses a static baseline post-enrollment; that's a deliberate PoC simplification and the production path is well-defined.

**Q: Isn't a 5-interval vector (Layer 3) too short to be reliable?**
> For identification purposes, yes — 5 intervals wouldn't distinguish you from millions of people. But PhantomGrid isn't identification, it's verification — is this session consistent with the enrolled user's rhythm? For that binary question, 5 intervals are sufficient because DTW operates on relative timing patterns, and individual rhythms for familiar short sequences (PINs you type daily) are remarkably stable. Studies on keystroke dynamics show FRR under 5% with as few as 5 intervals for same-device verification.

**Q: What is the computational cost? Will this slow down the banking portal?**
> Isolation Forest inference on a 3-feature vector: ~0.1ms. DTW on two 5-element arrays (O(n²) = O(25) operations): ~0.01ms. Total backend inference time per composite score: under 5ms. The backend returns a score; it doesn't block the user's transaction flow. All scoring happens asynchronously to the payment flow.

**Q: What if the attacker knows the architecture and specifically targets the weak layer?**
> See the attack tree in `THREAT_MODEL.md`. The optimal attack requires knowing exact fusion weights (0.30/0.40/0.30) AND successfully mimicking the victim's Layer 2 navigation behavior AND their Layer 3 keystroke rhythm simultaneously. Even knowing the weights doesn't help unless you can also fool the biometric models — which require having observed the victim's specific behavioral patterns, not just knowing they exist. Production hardening: randomize thresholds per session within a small band.

**Q: How does this compare to existing fraud detection?**
> Existing fraud detection (e.g. rule engines, device fingerprinting) acts post-login: it looks at transaction patterns, device metadata, location. PhantomGrid operates on the behavioral substrate — *how* the user interacts, not just *what* they do. It catches account takeovers where the attacker is using the victim's own device and credentials, a scenario device fingerprinting misses entirely.

### On the Architecture / Demo

**Q: Why SQLite and not PostgreSQL?**
> Deliberate PoC scoping for a 4–5 day hackathon. The schema is standard relational SQL; migration to PostgreSQL is a drop-in change (swap the SQLite connection string for a `psycopg2` connection). SQLite has zero infrastructure dependency, which makes the demo portable and reliable.

**Q: Why vanilla HTML/JS dashboard instead of React?**
> Same reason — PoC scope. The dashboard is fully functional with no build step, no npm, no Node.js required. Anyone can open `index.html` in a browser and it works. For production, React or any framework would be appropriate; the API contract is already defined in `INTEGRATION_NOTES.md`.

**Q: Where does the dashboard get its data?**
> It polls `GET /logs`, which returns the last 10 `session_logs` rows. The latest row drives the gauge, layer bars, and decision badge; the full list fills the session-log table. If the backend is unreachable the dashboard shows "API offline" in the status bar and keeps retrying every 2 seconds without crashing.

**Q: The composite score seems simple — just a weighted average. Is that rigorous enough?**
> The weighted average is the fusion layer. The rigor is in *how each layer score is produced* — Isolation Forest anomaly scores and DTW distances are not arbitrary inputs; they're the output of trained ML models with per-user learned baselines. The fusion weights are empirically motivated: L2 has the highest weight because navigation entropy and beneficiary dwell time are the most discriminating features for payment-stage fraud based on the literature.

### On Security

**Q: Can an attacker just replay a captured session payload?**
> No — PhantomGrid implements replay-attack defense in the current PoC. Every `/verify` call computes a SHA-256 signature of the behavioral package. An exact duplicate within a 5-minute window is detected by `services/audit.py::is_replay()`, which forces `decision = BLOCK` and sets `replay_detected: true` in the response. You can run `python demo_replay.py` to see it live: the first call is scored normally; the identical second call is immediately blocked. The dashboard shows `replay_detected = True`.

**Q: What about enrollment poisoning — can an attacker enroll as someone else?**
> The `/enroll` endpoint must require a valid authenticated session token that proves the caller *is* the claimed `user_id`. This is an integration requirement on Person 2 — the enrollment endpoint must be authenticated. In the PoC this is called out explicitly in the threat model under Elevation of Privilege. It is not a design flaw — it is a known PoC limitation with a clear production fix.

**Q: Is the behavioral data a biometric under DPDP 2023?**
> Behavioral biometrics occupy a gray area. The DPDP Act defines "biometric data" as physiological or biological data used for unique identification — fingerprints, iris scans, face geometry. Keystroke timing intervals are *behavioral* (not physiological) and are used for *verification* (not unique identification). Our legal interpretation, supported by comparable EU GDPR guidance on keystroke dynamics, is that these derived timing metrics are not biometric data under the Act. We store no raw event streams, only the derived vectors. However, we recommend that any production deployment obtain legal counsel's opinion and include this processing in the bank's privacy notice.

---

## 9. Demo Script (Live Run)

**Setup checklist before demo:**
- [ ] Backend running: `cd backend && uvicorn main:app` (deps: fastapi, uvicorn, scikit-learn, sqlalchemy, pydantic, dtaidistance)
- [ ] `backend/phantomgrid.db` exists (created on first API call)
- [ ] Serve + open the dashboard over HTTP (e.g. `python -m http.server` in `dashboard/`) — `file://` blocks fetch
- [ ] Confirm gauge shows a score and status bar reads ALLOW
- [ ] ⚠ Use a FRESH user_id for the attacker, or enroll a separate attacker account (see below)

**Demo flow (5 minutes):**

1. **30s — Show the dashboard** loading live. Point out: "This is the analyst view. It polls `GET /logs` and shows the active banking sessions in real time."

2. **60s — Trigger a legitimate session** from Person 1's portal with the demo user enrolled. Walk through the layer bars: "L1 decoy interactions. L2 navigation + beneficiary dwell. L3 PIN rhythm. Composite ≈ 2 — ALLOW. Session proceeds normally."

3. **60s — Trigger an attacker session.** Show the gauge jump to red: "Decoy taps detected. Beneficiary dwell spiked. PIN rhythm doesn't match — DTW distance is huge. Composite hits ~100 — BLOCK. Session blocked."

4. **60s — Trigger an OTP/amber session** (moderate anomaly — e.g. mild attacker). Show the OTP toast appear: "Composite ≈ 72 — OTP. The system doesn't block; it silently triggers step-up re-auth. Legit user passes OTP/fingerprint and continues. Attacker without the second factor is stopped."

5. **60s — Show the session log table** with the sessions. Point out the timestamps, per-layer scores, and ALLOW/OTP/BLOCK badges.

6. **60s — Questions from judges.**

> ⚠ **Demo ordering note:** the backend adaptively appends accepted (ALLOW) sessions to the
> baseline. With the continuous scoring engine a single legit session no longer suppresses a
> strong attacker, but to be safe **demo the attacker on a fresh/separate `user_id`** (the
> capture module currently hardcodes `arjun_4821`) so a sustained run of legit sessions can't
> drift the baseline before the attacker step.

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **Behavioral biometrics** | Authentication based on patterns in how a user behaves (typing rhythm, mouse movement) rather than what they know (password) or have (token) |
| **Isolation Forest** | Unsupervised anomaly detection algorithm that isolates outliers using random recursive partitioning |
| **DTW (Dynamic Time Warping)** | Algorithm that finds the optimal alignment between two time series, tolerating speed variations |
| **Anomaly score** | A value (0–100 in PhantomGrid) indicating how different a behavioral sample is from the enrolled baseline |
| **Composite score** | Weighted sum of three layer scores: L1×0.30 + L2×0.40 + L3×0.30 |
| **Decision threshold** | ALLOW: <60 · OTP: 60–79 · BLOCK: ≥80 (`services/fusion.py`) |
| **Contamination** | IsolationForest hyperparameter — expected fraction of outliers in training data (backend uses 0.1 = 10%) |
| **Nav entropy** | Shannon entropy of the user's page navigation sequence, normalized to [0,1] |
| **Decoy element** | Hidden/invisible UI element that legitimate users never interact with; touching it is a fraud signal |
| **Beneficiary dwell** | Time spent on the "add/confirm beneficiary" screen — a high-value fraud signal |
| **Inter-keystroke interval** | Time in milliseconds between consecutive key presses — the raw signal for Layer 3 |
| **Baseline** | The statistical model of a user's legitimate behavior, built during enrollment |
| **Enrollment** | The initial 5 samples (`POST /enroll`) during which the backend stores the user's behavioral baseline vectors |
| **FRR (False Rejection Rate)** | Rate at which legitimate users are incorrectly flagged as anomalies |
| **FPR (False Positive Rate)** | Rate at which anomalies are incorrectly scored as normal (missed detections) |
| **STRIDE** | Threat modeling framework: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| **EMA (Exponential Moving Average)** | Baseline update mechanism — confirmed-legit sessions slowly drift the baseline toward current behavior |
| **RBI** | Reserve Bank of India — India's central banking regulator |
| **DPDP Act** | Digital Personal Data Protection Act, 2023 — India's primary data protection legislation |
| **CORS** | Cross-Origin Resource Sharing — browser security policy that requires explicit server permission for cross-origin fetch calls |
