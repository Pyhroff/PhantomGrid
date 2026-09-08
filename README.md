# PhantomGrid — AI-Driven Passive Behavioural Authentication Engine

<p align="center">
  <img src="https://raw.githubusercontent.com/Pyhroff/PhantomGrid/master/architecture.svg" width="720" alt="PhantomGrid Architecture"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/scikit--learn-IsolationForest-orange" />
  <img src="https://img.shields.io/badge/DTW-dtaidistance-purple" />
  <img src="https://img.shields.io/badge/SQLite-Audit--Chained-lightgrey" />
  <img src="https://img.shields.io/badge/Tests-8%2F8%20passing-brightgreen" />
  <img src="https://img.shields.io/badge/Detection-95.3%25-red" />
</p>

> **CBI Hackathon 2026 — Phase II Submission**
> Team: **ZeroIntent** · S.No: **8** · Indian Institute of Information Technology Kottayam

---

## What Is PhantomGrid?

PhantomGrid is a three-layer **passive behavioural authentication engine** that runs silently beneath a banking portal. It authenticates users **continuously** — not just at login — by watching *how* they interact rather than *what* they know.

An attacker with stolen credentials, a cloned OTP, and even the correct PIN **still cannot get in** — because their behavioural fingerprint is wrong.

> **The killer insight:** You can steal a password. You cannot steal a rhythm.

### Core Properties

| Property | Detail |
|----------|--------|
| **Passive** | Zero friction — users do nothing extra |
| **Continuous** | Every session scored end-to-end, not just at login |
| **Explainable** | Per-layer risk breakdown shown to the analyst |
| **Tamper-evident** | SHA-256 hash-chained audit log — RBI-grade |
| **Self-aware** | Baseline maturity indicator — honest about confidence |
| **Replay-proof** | SHA-256 payload signatures block packet-replay attacks |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│           Browser — NexaBank Portal (Madapati Jyothiradithya)    │
│  capture.js: onDecoyTap · onBeneDwell · onAmountKey · onPinKey   │
│  Sends ONE behavioural JSON package per transaction              │
└─────────────────────────────┬────────────────────────────────────┘
                              │  POST /enroll | POST /verify
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                 FastAPI Backend — ML Inference Engine            │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Layer 1        │  │  Layer 2        │  │  Layer 3        │  │
│  │  CognitiveTrap  │  │  IntentTrace    │  │  RhythmLock     │  │
│  │  Isolation      │  │  Isolation      │  │  Dynamic Time   │  │
│  │  Forest + Dev   │  │  Forest + Dev   │  │  Warping (DTW)  │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                   │                     │            │
│           └───────────────────┼─────────────────────┘            │
│                               ▼                                  │
│                  Composite Fusion Engine                         │
│                  L1×0.30 + L2×0.40 + L3×0.30                    │
│                               │                                  │
│              ┌────────────────┼────────────────┐                 │
│              ▼                ▼                ▼                 │
│           ALLOW             OTP            BLOCK                 │
│          (< 60)          (60–79)          (≥ 80)                 │
│                               │                                  │
│              Replay Defence + Tamper-Evident Audit Chain         │
│              SQLite: user_profiles + session_logs                │
└──────────────────────────────┬───────────────────────────────────┘
                               │  GET /logs (polls every 2s)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│              Analyst Dashboard — Real-Time Monitoring             │
│  Live gauge · Layer bars · WHY THIS DECISION panel               │
│  OTP toast · BLOCK alert + beep · 🛡 Audit verified badge       |
│  Baseline maturity indicator · Session log table                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## The Three Layers

### Layer 1 — CognitiveTrap (Isolation Forest)

Detects interaction with **invisible decoy elements** embedded in the banking UI. Legitimate users who know the interface never touch them. Attackers exploring unfamiliar territory do.

- Signal: `decoy_tap_count`, `amount_hesitations`
- Model: Isolation Forest (unsupervised, per-user baseline)
- Scoring: Continuous 0–100 via anomaly gate + normalized deviation magnitude

### Layer 2 — IntentTrace (Isolation Forest)

Profiles **navigation intent** through beneficiary dwell time and amount-field typing rhythm. Fraudulent sessions display characteristic hesitation and exploration patterns.

- Signal: `bene_dwell_ms`, `avg(amount_iki)`
- Model: Isolation Forest (per-user baseline, 5-sample enrollment)
- Scoring: Continuous 0–100

### Layer 3 — RhythmLock (Dynamic Time Warping)

Captures the **inter-keystroke intervals** (ms) of the user's PIN entry — a behavioural biometric that encodes muscle memory, cognitive rhythm, and motor patterns unique to each individual.

- Signal: `pin_vector` (5 inter-key gaps for a 6-digit PIN)
- Algorithm: Dynamic Time Warping — tolerates natural speed variation (10% faster when rushed = still you)
- Scoring: `min(100, dtw_distance / 180 × 100)` — smooth, monotonic

### Fusion

```
composite = L1 × 0.30 + L2 × 0.40 + L3 × 0.30

composite < 60  →  ALLOW  (green)
60 ≤ c < 80    →  OTP    (amber — silent step-up re-auth)
composite ≥ 80  →  BLOCK  (red — transaction stopped)
```

---

## Advanced Security Features

### Replay-Attack Defence
Every `/verify` payload is SHA-256 signed. An exact duplicate within a 5-minute window is detected by `services/audit.py::is_replay()` → forced BLOCK + `replay_detected: true` in response.

```bash
python demo_replay.py   # Live demo: first call scores, second is blocked
```

### Tamper-Evident Audit Trail
Each `session_logs` row contains `row_hash` (SHA-256 of its own content) and `prev_hash` (hash of the previous row), forming a cryptographic hash chain. Editing any single row invalidates the entire chain from that point forward.

```bash
python verify_audit.py --tamper   # Mutates a row, detects it, restores it
GET /audit/verify                  # API endpoint: {valid, broken_at_session}
```

### Baseline Maturity Indicator
```bash
GET /maturity?user_id=X
# → {samples: 4, required: 5, mature: false, confidence: "low"}
```
Disarms the cold-start question — the system knows when to trust itself.

### Adaptive Learning
Every ALLOW session is appended to the user's baseline (sliding window of 20). The model slowly drifts with legitimate behavioural change (new device, lifestyle shift) while remaining resistant to targeted gradual poisoning.

---

## Performance Benchmark

Validated on a 300-session synthetic cohort (150 legit, 150 attacker):

| Metric | Result |
|--------|--------|
| Detection Rate (TPR) | **95.3%** |
| False Positive Rate | **0.0%** |
| AUC (ROC) | **1.00** |

```bash
python benchmark.py          # Regenerate results
open benchmark_report.html   # ROC curve + confusion matrix
```

---

## Project Structure

```
PhantomGrid/
├── backend/
│   ├── main.py                  # FastAPI application — all endpoints
│   ├── database.py              # SQLAlchemy engine + session
│   ├── database_models.py       # ORM models: UserProfile, SessionLog
│   ├── schemas.py               # Pydantic request/response models
│   └── services/
│       ├── scoring.py           # Continuous scoring engine
│       ├── audit.py             # Replay defence + hash chain
│       ├── fusion.py            # Weighted fusion + ALLOW/OTP/BLOCK
│       ├── layer1.py            # CognitiveTrap scorer
│       ├── layer2.py            # IntentTrace scorer
│       └── layer3.py            # RhythmLock DTW scorer
│
├── frontend/
│   ├── Nexa_bank_demoUI.html    # NexaBank banking portal UI
│   └── capture.js               # Behavioural signal capture hooks
│
├── dashboard/
│   └── index.html               # Live analyst dashboard
│
├── tests/
│   ├── conftest.py              # Fixtures: fresh_user, enroll_user, verify
│   └── test_integration.py      # 8 integration tests against live backend
│
├── threat_model/
│   └── THREAT_MODEL.md          # STRIDE + DFD + risk matrix + attack trees
│
├── demo_legit.py                # Guaranteed ALLOW demo script
├── demo_attacker.py             # Guaranteed BLOCK demo script
├── demo_replay.py               # Replay attack demonstration
├── verify_audit.py              # Tamper-evident audit demonstration
├── benchmark.py                 # 300-session ROC/AUC benchmark
├── benchmark_report.html        # Benchmark visualisation
├── config.py                    # Central configuration
├── architecture.svg             # System architecture diagram
├── DEMO_RUNBOOK.md              # Complete demo-day runbook
└── README.md                    # This file
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Pyhroff/PhantomGrid.git
cd PhantomGrid
```

### Step 2 — Install Dependencies

```bash
pip install fastapi "uvicorn[standard]" scikit-learn sqlalchemy pydantic dtaidistance requests pytest matplotlib numpy
```

No virtual environment required. All dependencies are pure Python or have pre-built wheels for Windows/Linux/macOS.

### Step 3 — Verify Installation

```bash
python -c "import fastapi, sklearn, dtaidistance, sqlalchemy; print('All dependencies OK')"
```

---

## Configuration

All configuration lives in `config.py`:

```python
BASE_URL   = "http://127.0.0.1:8000"   # Change to Railway URL for remote demo
DEMO_USER  = "demo_user"
ALLOW_MAX  = 60                          # composite < 60  → ALLOW
BLOCK_MIN  = 80                          # composite ≥ 80  → BLOCK
WEIGHTS    = (0.30, 0.40, 0.30)         # L1, L2, L3 fusion weights
```

The SQLite database is created automatically at `backend/phantomgrid.db` on first startup. No manual database setup required.

---

## Running the Application

### Terminal 1 — Start the Backend

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Wait for:
```
Application startup complete.
```

Swagger UI (interactive API docs): `http://127.0.0.1:8000/docs`

### Terminal 2 — Start the Dashboard Server

```bash
cd dashboard
python -m http.server 5599
```

Open browser → `http://localhost:5599`

### Browser — Open the Bank Portal

```
frontend/Nexa_bank_demoUI.html?enroll=true
```

For enrollment mode (first 5 sessions), include `?enroll=true`. The enrollment banner appears at the top tracking progress (Session X of 5). After 5 sessions, the system automatically switches to live scoring mode.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/enroll` | Store one behavioural enrollment sample |
| `POST` | `/verify` | Score a live session → ALLOW/OTP/BLOCK |
| `GET` | `/logs` | Last 10 session log rows |
| `GET` | `/maturity?user_id=X` | Baseline maturity for a user |
| `GET` | `/audit/verify` | Walk hash chain → `{valid, broken_at_session}` |

### Request Body (`/enroll` and `/verify`)

```json
{
  "user_id": "arjun_4821",
  "decoy_tap_count": 0,
  "amount_hesitations": 0,
  "bene_dwell_ms": 610,
  "amount_iki": [110, 95, 105],
  "pin_vector": [118, 92, 107, 85, 99]
}
```

### Response (`/verify`)

```json
{
  "layer1_score": 4.4,
  "layer2_score": 1.4,
  "layer3_score": 0.0,
  "composite_score": 1.9,
  "decision": "ALLOW",
  "replay_detected": false
}
```

---

## Demo Scripts

```bash
# Enroll a fresh user + verify as legitimate → ALLOW
python demo_legit.py

# Enroll a fresh user + verify as attacker → BLOCK (dashboard flashes red)
python demo_attacker.py

# Show replay attack defence (identical payload = BLOCK)
python demo_replay.py

# Demonstrate tamper-evident audit chain
python verify_audit.py --tamper

# Run 300-session benchmark → regenerate ROC curve + confusion matrix
python benchmark.py
```

---

## Running Tests

With the backend running on port 8000:

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_integration.py::test_legit_session_allows                    PASSED
tests/test_integration.py::test_clean_attacker_blocks                   PASSED
tests/test_integration.py::test_layer3_rhythm_mismatch_is_high          PASSED
tests/test_integration.py::test_layer1_decoy_taps_flag                  PASSED
tests/test_integration.py::test_attacker_blocks_even_after_legit_session PASSED
tests/test_integration.py::test_fusion_weights_and_thresholds            PASSED
tests/test_integration.py::test_verify_rejects_missing_user_id           PASSED
tests/test_integration.py::test_session_logged_after_verify              PASSED

8 passed in ~10s
```

Tests auto-skip if the backend is offline. Each test uses an isolated `fresh_user` (UUID-based) — no cross-test baseline pollution.

---

## Test Credentials

| User | Role | How to enroll |
|------|------|---------------|
| `arjun_4821` | Demo user (bank UI) | Open bank UI with `?enroll=true`, complete 5 payment flows |
| `demo_user` | Script user | Handled automatically by demo scripts |
| `t_<uuid>` | Test users | Handled automatically by pytest fixtures |

---

## Environment Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.12 |
| RAM | 512 MB | 2 GB |
| Disk | 100 MB | 500 MB |
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Any modern |
| Browser | Any modern (Chrome/Edge/Firefox) | Chrome |

No Docker, no Redis, no cloud service required. Fully self-contained on a single machine.

---

## Software Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥ 0.111 | REST API framework |
| `uvicorn[standard]` | ≥ 0.29 | ASGI server |
| `scikit-learn` | ≥ 1.4 | IsolationForest (L1, L2 anomaly detection) |
| `dtaidistance` | ≥ 2.3 | Dynamic Time Warping (L3 rhythm comparison) |
| `sqlalchemy` | ≥ 2.0 | ORM + SQLite session management |
| `pydantic` | ≥ 2.0 | Request/response validation |
| `requests` | ≥ 2.31 | HTTP client (tests + demo scripts) |
| `pytest` | ≥ 8.0 | Integration test runner |
| `matplotlib` | ≥ 3.8 | Benchmark ROC/confusion matrix plots |
| `numpy` | ≥ 1.26 | Synthetic session generation (benchmark) |

---

## AI / Generative AI Disclosure

This project uses the following AI/ML components:

| Model / Algorithm | Library | Role |
|-------------------|---------|------|
| **Isolation Forest** | `scikit-learn` | Unsupervised anomaly detection for Layer 1 (CognitiveTrap) and Layer 2 (IntentTrace). Trained per-user on 5 enrollment samples. |
| **Dynamic Time Warping** | `dtaidistance` | Time-series alignment for Layer 3 (RhythmLock) PIN rhythm comparison. |
| **Continuous Scoring Engine** | Custom (`services/scoring.py`) | Replaces IF saturation on small baselines with a gate + normalized-deviation magnitude hybrid. |
| **Adaptive Baseline Update** | Custom (online learning) | Confirmed-ALLOW sessions appended to baseline (sliding window 20). Model drifts with legitimate behavioural change. |

No generative AI (LLMs, diffusion models, etc.) is used. All ML is classical/statistical and fully explainable.

---

## Third-Party Acknowledgements

| Component | Licence |
|-----------|---------|
| FastAPI | MIT |
| scikit-learn | BSD-3 |
| dtaidistance | Apache 2.0 |
| SQLAlchemy | MIT |
| Pydantic | MIT |
| Uvicorn | BSD-3 |
| Matplotlib | PSF |
| NumPy | BSD-3 |

---

## Security & Compliance

- **No PII stored** — PIN digits never persisted; only millisecond timing intervals
- **Data localisation ready** — SQLite on-device; production path: `aws ap-south-1` / `azure centralindia`
- **DPDP Act 2023** — Behavioral timing vectors are derived metrics, not physiological biometrics
- **RBI Master Direction (2021)** — Risk-based step-up authentication (OTP triggered at 60–79, not blanket)
- **Tamper-evident audit** — SHA-256 hash chain on `session_logs` satisfies audit trail requirements

---

## Demo Video

The demo video (`Demo Video PhantomGrid.mp4`) is included in this submission ZIP. It demonstrates:

1. Live legitimate session — dashboard scores **ALLOW** (composite ~2)
2. Attacker with correct credentials — gauge reaches 100 — **BLOCK** fires
3. Replay attack defence — duplicate payload detected, forced **BLOCK**
4. Tamper-evident audit chain — single row edit detected, chain invalidated
5. Full integration test suite — **8/8 passed** against live backend

🌐 **Run locally:** `uvicorn main:app --host 127.0.0.1 --port 8000` from `backend/`, then [Swagger UI](http://127.0.0.1:8000/docs)

---

## Expected Impact & ROI

| Metric | Value |
|--------|-------|
| PSB account holders at risk | 600M+ |
| Annual digital fraud loss (PSBs) | ₹7,400 crore |
| PhantomGrid detection rate | **95.3%** |
| False positive rate | **0.0%** |
| Estimated fraud prevented (at 95.3% detection) | ~₹7,050 crore/year |
| Extra friction added for legitimate users | **Zero** |
| Infrastructure cost to deploy | **Zero** (JS snippet + API server) |
| Time to integrate into existing banking portal | **< 1 day** |

PhantomGrid catches account takeovers **before money moves** — not after the transaction is flagged by fraud analytics. This shifts the defence from reactive to real-time, closing the window that costs PSBs crores daily.

---

## Team

| Role | Name | Institute |
|------|------|-----------|
| Frontend — Behavioural Signal Capture | **Madapati Jyothiradithya** | IIIT Kottayam |[GitHub](https://github.com/Adithya9x) |
| Backend — ML Engine + FastAPI | **Kontheti Sai Akhilesh** | IIIT Kottayam |[GitHub](https://github.com/SaiAkhilesh026) |
| Dashboard + Tests + Threat Model + Security (Lead) | **Praising Y Harris Ratnam** | IIIT Kottayam |[GitHub](https://github.com/Pyhroff) |

**Team ZeroIntent** · S.No. 8 · CBI Hackathon 2026 · MNNIT Allahabad

---

## License

MIT License. See `LICENSE` for details.

---

<p align="center">
  <i>Passive. Invisible. Unbeatable.</i>
</p>
