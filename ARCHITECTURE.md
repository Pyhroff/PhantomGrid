# PhantomGrid — Complete Architecture (Person 1 → Person 2 → Person 3)

**Team ZeroIntent · PSBs Hackathon 2026 · IIIT Kottayam (hosted at MNNIT Allahabad)**
Everything, end to end, so you can present any part with confidence.

---

## 0. One-paragraph pitch

PhantomGrid is a **passive, three-layer behavioural authentication mesh** that wraps an
existing bank session. After login, it keeps verifying that the person *operating* the
session is the real account holder — not by what they know (PIN) but by **how they behave**:
how they navigate, how they hesitate, and the **rhythm of their PIN keystrokes**. Three
independent signals are scored by ML, fused into one risk number, and turned into a
decision — **ALLOW**, **OTP step-up**, or **BLOCK** — in real time, with zero added friction
for genuine users.

**The killer line:** *an attacker can have the correct PIN and still be blocked*, because
their typing **rhythm** doesn't match.

---

## 1. The problem & the insight

- **Problem:** Account Takeover (ATO). OTP/PIN/password are **point-in-time gates**. Once an
  attacker clears login (stolen credentials, SIM-swap, session hijack), they face **zero**
  behavioural resistance for the rest of the session.
- **Insight:** behaviour is continuous and hard to steal. Navigation habits, hesitation, and
  keystroke rhythm form a fingerprint that persists *throughout* the session.

---

## 2. High-level architecture

Three components, one backend brain (see `architecture.svg`):

```
  CLIENT (untrusted)                 ║  BACKEND (trusted)
  Browser: NexaBank UI + capture.js  ║  FastAPI  →  L1·L2·L3 scorers  →  fusion
        │ POST /enroll ×5            ║      │  reads/writes
        │ POST /verify  ────────────►║      ▼
        │◄── decision + scores ──────║   SQLite (user_profiles, session_logs)
  Bank UI: ALLOW / OTP / BLOCK       ║      ▲
                                     ║      │ GET /logs (every 2s)
  Analyst Dashboard ◄────────────────╨──────┘
```

| Layer | Owner | Tech |
|-------|-------|------|
| Frontend (capture + bank UI + re-auth) | **Person 1** | Vanilla JS, HTML5 Canvas, WebAuthn/OTP |
| Backend (API + ML + DB) | **Person 2** | FastAPI, scikit-learn, dtaidistance (DTW), SQLite |
| Analyst layer (dashboard + threat model + tests + metrics) | **Person 3** | Vanilla JS dashboard, pytest, Chart.js, STRIDE |

---

## 3. PERSON 1 — Frontend (signal capture + bank UI + re-auth)

**Files:** `frontend/Nexa_bank_demoUI.html`, `frontend/capture.js`

### 3.1 The bank UI (`Nexa_bank_demoUI.html`)
A realistic "NexaBank" web-banking portal: Home / Transfer / Cards / Invest / Profile.
The demo happens in **Transfer**: pick a beneficiary → enter an amount → type the 6-digit
PIN → Confirm & Pay. The account is hard-coded to user **`arjun_4821`**.

### 3.2 The capture module (`capture.js`) — the heart of Person 1
Injected via `<script src="capture.js">`. It silently captures behaviour through DOM event
hooks and assembles one **signal package** at payment time:

| Hook | Captures | Feeds |
|------|----------|-------|
| `onDecoyTap(name)` | taps on invisible **decoy** elements a real user never touches | L1 `decoy_tap_count` |
| `onAmountKey(ts)` | inter-key gaps while typing the **amount**; gaps >300ms = a "hesitation" | L1 `amount_hesitations`, L2 `amount_iki` |
| `onBeneDwell(idx,ms)` | how long the user **dwells** on a beneficiary before selecting | L2 `bene_dwell_ms` |
| `onPinKey(digit,ms)` | inter-key **rhythm** of the 6-digit PIN (5 intervals, ms) | L3 `pin_vector` |
| `onPaySubmit(payload)` | bundles everything and POSTs to the backend | — |

**The signal package** sent to the backend:
```json
{ "user_id": "arjun_4821",
  "decoy_tap_count": 0, "amount_hesitations": 0,
  "bene_dwell_ms": 600, "amount_iki": [110,95,105],
  "pin_vector": [118,92,107,85,99] }
```

### 3.3 Enrollment mode
`capture.js` tracks **enroll vs verify** via `localStorage('pg_enroll_mode')`. The first 5
payments POST to **`/enroll`** (building the baseline). After 5 it flips to **`/verify`**
(scoring). Adding `?enroll=true` to the URL shows a progress banner "Session X of 5".

### 3.4 Re-auth (the OTP / WebAuthn step-up)
When the backend returns **OTP**, `capture.js` triggers a **step-up challenge** — a
WebAuthn fingerprint prompt with an **OTP overlay fallback** (`showOTPOverlay()`,
`onOTPVerified()`). On **BLOCK** it terminates the transaction; on **ALLOW** it proceeds
silently. *(Re-auth is wired to the bank's existing OTP infra — PhantomGrid only triggers
the challenge, it doesn't send OTPs itself.)*

---

## 4. PERSON 2 — Backend (API + ML engine + database)

**Files:** `backend/main.py`, `schemas.py`, `database.py`, `database_models.py`,
`services/{layer1,layer2,layer3,scoring,fusion}.py`

### 4.1 API endpoints (FastAPI, base `http://127.0.0.1:8000`)
| Endpoint | Purpose |
|----------|---------|
| `POST /enroll` | store one baseline sample (5 needed); after 5, enrollment is complete |
| `POST /verify` | score a live session → `{layer1_score, layer2_score, layer3_score, composite_score, decision}` |
| `GET /logs` | last 10 session rows (for the analyst dashboard) |

CORS is open (`allow_origins=["*"]`) so the dashboard can poll from any origin.

### 4.2 Enrollment logic (`/enroll`)
Collects **5 samples** per `user_id`, stored as JSON vectors in `user_profiles`:
`layer1_vectors`, `layer2_vectors`, `pin_vectors`. Under 5 → "Sample N/5 stored"; at 5 →
"Enrollment complete".

### 4.3 The three scorers
Each layer outputs a **continuous 0–100 risk** (higher = more suspicious):

- **Layer 1 — CognitiveTrap** (`layer1.py`): IsolationForest over `[decoy_tap_count,
  amount_hesitations]`. Real users tap no decoys and don't hesitate → low; attackers reading
  the UI fresh → high.
- **Layer 2 — IntentTrace** (`layer2.py`): IsolationForest over `[bene_dwell_ms,
  avg(amount_iki)]`. Habitual users move fast on familiar contacts/amounts; attackers linger.
- **Layer 3 — RhythmLock** (`layer3.py`): **Dynamic Time Warping (DTW)** distance between the
  live `pin_vector` and the enrolled baseline. A different person's rhythm → large distance →
  high risk. **This is the signal that catches a correct-PIN attacker.**

### 4.4 Continuous scoring engine (`services/scoring.py`) — *Person 3 upgrade, see §5.6*
IsolationForest's raw output **saturates** on tiny baselines (it can't tell mild from severe).
The engine keeps IsolationForest as the **anomaly gate** but adds a **normalized deviation
magnitude**, so scores ramp **smoothly 0–100** instead of snapping to fixed buckets. DTW is
mapped continuously too. This is why the gauge now shows real gradation (e.g. 1.9 → 72 → 100).

### 4.5 Fusion & decision (`services/fusion.py`)
```
composite = 0.30·L1 + 0.40·L2 + 0.30·L3      (L2 weighted highest — intent matters most)
ALLOW  if composite < 60      (green  — proceed, zero friction)
OTP    if 60 ≤ composite < 80 (amber  — step-up re-auth)
BLOCK  if composite ≥ 80      (red    — terminate + alert)
```

### 4.6 Database (SQLite, `backend/phantomgrid.db`)
- `user_profiles(user_id, layer1_vectors, layer2_vectors, pin_vectors)` — baselines (JSON).
- `session_logs(session_id, timestamp, user_id, layer1_score, layer2_score, layer3_score,
  composite_score, decision)` — every `/verify` writes one row.

### 4.7 Adaptive learning
On every **ALLOW**, the new sample is appended to the baseline (sliding window up to 20
samples), so the profile adapts to natural drift (typing speed, device) without re-enrollment.

---

## 5. PERSON 3 — Analyst layer (yours)

### 5.1 Analyst Dashboard (`dashboard/index.html`)
Self-contained, no build step. Polls **`GET /logs`** every 2s; the latest row drives the live
widgets, the list fills the table. Elements:
- **Composite gauge** (0–100, colour-coded green/amber/red) + decision word.
- **WHY THIS DECISION** ✨ — per-layer plain-English reasons (explainability).
- **Session Log** — last 10 with L1/L2/L3, composite, decision badges.
- **L1/L2/L3 live bars** (CognitiveTrap / IntentTrace / RhythmLock).
- **Status bar** — flashes amber on OTP, red on BLOCK.
- **OTP toast** ✨ and **full-screen BLOCK alert + beep** ✨ — the dramatic moments.

### 5.2 Benchmark report (`benchmark_report.html` + `benchmark.py`)
Generates 100+ legit & 100+ attacker sessions, runs them through the engine, and reports
**detection rate, false-positive rate, accuracy, ROC AUC, confusion matrix, ROC curve** —
turning the proposal's claims into **measured evidence**.

### 5.3 Threat model (`threat_model/THREAT_MODEL.md`)
STRIDE table (6 threats × attack × mitigation), a **Data-Flow Diagram with trust
boundaries**, a **risk matrix** (likelihood × impact), two **attack trees**, residual risks,
and an RBI/DPDP **compliance** note.

### 5.4 Integration tests (`tests/`)
8 pytest tests against the live backend: legit→ALLOW, attacker→BLOCK, layer behaviour,
fusion math, validation (422), and `/logs` persistence. **8/8 pass.**

### 5.5 Demo tooling
`demo_attacker.py` (→ guaranteed BLOCK), `demo_legit.py` (→ guaranteed ALLOW),
`DEMO_RUNBOOK.md` (stage script), `OPERATOR_GUIDE.md` (how to run everything),
`architecture.svg` (this diagram).

### 5.6 Risk-engine upgrade (`CHANGELOG_RISK_ENGINE.md`)
Replaced the 4-bucket layer scoring with the continuous engine (§4.4), fixed the L2 ceiling,
moved decision bands to 60/80, and made the demo **order-independent** (an attacker now BLOCKs
even after a legit session — the old scoring dropped to OTP).

### 5.7 Integration contract (`INTEGRATION_NOTES.md`)
The exact API shapes, the real endpoints, and the teammate bugs found (Person 1's result-modal
breakdown mismatch; `capture.js`'s call to an unimplemented `/reauth-log`).

---

## 6. End-to-end lifecycle (walk a judge through this)

**Legit session:**
1. You navigate normally, type your PIN at your natural rhythm, Confirm & Pay.
2. `capture.js` packages the signals → `POST /verify`.
3. Backend: L1≈4, L2≈1, L3≈0 → composite ≈ 2 → **ALLOW**.
4. Bank UI: "Payment Authorized". Dashboard: green, "all signals within baseline". Zero friction.

**Attacker session (same account):**
1. Attacker taps decoys, hesitates, types the correct PIN with the **wrong rhythm**.
2. `POST /verify`.
3. Backend: L1=100, L2=100, **L3=100 (rhythm mismatch)** → composite=100 → **BLOCK**.
4. Bank UI: "Transaction Blocked". Dashboard: gauge slams to 100, **red flash + beep**, WHY
   panel names the reasons. *Stolen PIN wasn't enough.*

**OTP middle case:** a borderline session (composite 60–79) → **OTP step-up** challenge
(amber toast), proceeds only if re-auth passes.

---

## 7. Tech stack & decision logic (cheat sheet)

```
Frontend : Vanilla JS (ES6), HTML5 Canvas (decoys), WebAuthn/OTP step-up
Backend  : Python 3.12, FastAPI, scikit-learn (IsolationForest), dtaidistance (DTW), SQLite
Analyst  : Vanilla JS dashboard, Chart.js (ROC), pytest, STRIDE

Fusion   : 0.30·L1 + 0.40·L2 + 0.30·L3
Bands    : ALLOW <60 · OTP 60–79 · BLOCK ≥80
Layers   : L1 CognitiveTrap (IF) · L2 IntentTrace (IF) · L3 RhythmLock (DTW)
```

---

## 8. Security & compliance posture (for bank judges)
- **No PII stored** — only anonymized behavioural vectors (timings, counts). Satisfies RBI
  data-localisation / DPDP.
- **Explainable** — every decision is attributable per layer (audit-ready).
- **Defence-in-depth** — three independent signals; defeating one isn't enough.
- **Zero friction** — invisible to genuine users; only surfaces on a real threat.

## 9. Honest limitations (have these ready for Q&A)
- **Cold-start:** 5-sample baseline; needs natural variance, matures with use. *(See the
  baseline-maturity feature if built.)*
- **Per-request model refit** → higher latency than the proposal's <15ms; production fits once
  at enrollment.
- **Device-specific rhythm:** enroll on the device you'll use; mobile needs its own baseline.
- **L2 IsolationForest** is the weakest signal (saturates); DTW (L3) is the strongest.
