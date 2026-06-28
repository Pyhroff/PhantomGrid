# PhantomGrid — STRIDE Threat Model

**System:** PhantomGrid Passive Behavioural Authentication PoC  
**Team:** ZeroIntent | PSBs Hackathon 2026  
**Author:** Person 3 (Analyst)  
**Date:** June 2026  

---

## 1. System Boundaries

### In Scope
| Component | Description |
|-----------|-------------|
| Browser JS (Person 1) | Captures raw behavioural events; sends to FastAPI |
| FastAPI backend (Person 2) | Scores events, runs ML models, persists sessions |
| SQLite database | Stores enrolled baselines and session logs |
| Analyst Dashboard | Reads composite scores; polls session logs |
| Scoring pipeline | Isolation Forest (L1/L2), DTW (L3), fusion weights |

### Out of Scope
| Component | Reason |
|-----------|--------|
| Bank's core auth infra (OTP, password) | PhantomGrid is a passive second layer — not a replacement |
| Network transport security (TLS) | Assumed handled by bank's gateway in production |
| HSM / key management | PoC scope; production hardening is a separate workstream |
| User device OS / browser security | Threat exists but is a platform-level concern |

**Trust boundary:** The primary trust boundary runs between the browser (untrusted) and the FastAPI backend (trusted). Any data arriving at `/enroll/*` or `/score/*` must be treated as potentially adversarial.

---

## 2. Assets

| Asset | Value | Location |
|-------|-------|----------|
| Behavioural baseline models | High — fingerprint of legitimate user; compromise enables impersonation | `user_baselines.layer1_model`, `layer2_model`, `layer3_vector` in SQLite |
| PIN rhythm vectors (Layer 3) | High — biometric-equivalent; irreplaceable if stolen | `user_baselines.layer3_vector` |
| Session logs | Medium — reveals usage patterns, risk scores, anomaly thresholds | `session_logs` table |
| Scoring API endpoints | High — if bypassed or poisoned, all downstream decisions are wrong | FastAPI at `localhost:8000` |
| Fusion weights & thresholds | Medium — knowledge of L1×0.30 + L2×0.40 + L3×0.30 and Green<60/Amber 60–84/Red≥85 helps attackers calibrate evasion | Hardcoded in backend logic |
| `user_id` namespace | Medium — predictable IDs allow cross-user baseline poisoning | Request bodies |

---

## 3. STRIDE Table

| Threat | Example Attack Against PhantomGrid | PhantomGrid Mitigation |
|--------|-------------------------------------|------------------------|
| **Spoofing** | Attacker captures a legitimate session's behavioural event JSON (L1/L2/L3 payloads) via network sniff and replays them verbatim to `/score/*` to obtain a green result. | Bind sessions to a short-lived signed session token issued at login. Include a server-side timestamp window check — events older than 30s are rejected. L3 DTW compares rhythm *variance* across multiple intervals, making exact replay detectable. |
| **Tampering** | Attacker performs a MITM between the browser and FastAPI (or patches the local JS) to modify the `composite_score` response before it reaches the dashboard or decision engine — changing `"decision":"red"` to `"decision":"green"`. | Sign API responses with an HMAC keyed to the session token. Dashboard and any downstream consumer must verify the signature before acting on the decision field. In PoC, at minimum run FastAPI over HTTPS even on localhost. |
| **Repudiation** | Attacker completes a fraudulent transaction and later claims the session never happened; without an immutable audit trail the bank cannot prove otherwise. | Every call to `/risk/composite` writes a row to `session_logs` with `session_id`, `user_id`, `timestamp`, all three layer scores, and the decision. In production, stream these logs to an append-only audit store (e.g., WORM S3 bucket or an immutable audit DB) so they cannot be deleted or modified after the fact. |
| **Information Disclosure** | Attacker gains read access to `phantomgrid.db` (e.g., via path traversal, misconfigured file permissions, or a compromised server) and exfiltrates the serialised Isolation Forest models and DTW vectors for all enrolled users. | Encrypt the SQLite file at rest (SQLCipher). Store serialised model blobs with per-user encryption keys derived from a KDF seeded by the bank's HSM. Never expose raw model bytes through any API endpoint. Restrict file-system permissions so only the FastAPI process UID can read the DB file. |
| **Denial of Service** | Attacker floods `/score/layer3` with thousands of requests per second. Each call triggers DTW inference (O(n²) in interval length), exhausting CPU and making the service unavailable for legitimate users. | Rate-limit per `user_id` and per source IP at the API gateway layer (e.g., 10 score requests/minute/user). Add request queue depth monitoring; shed load with HTTP 429 before inference is invoked. For PoC, FastAPI's `slowapi` middleware provides per-route rate limiting with two lines of code. |
| **Elevation of Privilege** | Attacker sends `/enroll/layer3` with `user_id=admin_user` (or another high-value target), injecting a new baseline that matches the attacker's own rhythm — so all subsequent attacker sessions score green for the victim account. | Enrolment endpoints must require a valid, authenticated session token that proves the caller *is* the claimed `user_id`. Never accept a `user_id` in the body without server-side identity verification. Implement enrolment rate-limiting and anomaly detection on baseline deltas (if a baseline changes dramatically, flag for manual review). |

---

## 4. Attack Trees

### Tree 1 — Attacker Bypasses Layer 3 (RhythmLock)

```
[GOAL] Score Green on /score/layer3 without knowing victim's PIN rhythm
│
├─[A] Obtain the enrolled DTW vector directly
│    ├─[A1] Exfiltrate SQLite DB  ──── requires server compromise (high effort)
│    └─[A2] Leak via API bug      ──── requires undisclosed endpoint vuln
│
├─[B] Replay a captured legitimate session
│    ├─[B1] Sniff network traffic ──── mitigated by HTTPS + session binding
│    └─[B2] Steal from browser JS ──── requires device compromise
│
├─[C] Brute-force a matching rhythm
│    ├─[C1] 5 intervals, each ~50–400ms, DTW tolerance ±15%
│    └─[C2] Search space: ~(350/15)^5 ≈ 5×10^10  ──── computationally infeasible per session
│
└─[D] Poison the baseline during enrolment
     ├─[D1] Exploit missing auth on /enroll/layer3  ──── mitigated by session-token check
     └─[D2] Gradual drift attack (submit similar intervals over many sessions)
              └─ Detected by monitoring baseline delta magnitude over time
```

### Tree 2 — Attacker Defeats Composite Score Without Triggering Red

```
[GOAL] composite_score < 85 despite being an attacker
│   Fusion: L1×0.30 + L2×0.40 + L3×0.30
│   Red threshold: ≥ 85
│
├─[A] Score perfectly on two layers, sacrifice one
│    e.g. L1=0, L2=0, L3=100 → composite = 0+0+30 = 30  ──── GREEN
│    └─ Requires knowing L2 behaviour in detail (high skill) AND L3 baseline (very high skill)
│
├─[B] Score Amber on all three layers
│    e.g. L1=84, L2=84, L3=84 → composite = 84  ──── AMBER (not Red)
│    └─ Attacker must precisely control all three simultaneous behavioural signals
│       while adapting to an unknown victim baseline  ──── extremely hard without prior data
│
├─[C] Exploit fusion weight knowledge to optimise
│    L2 has highest weight (0.40) — focus on passing L2
│    e.g. L1=90, L2=60, L3=90 → composite = 27+24+27 = 78  ──── AMBER
│    └─ Requires attacker to know exact weights; add weight obfuscation or randomisation in production
│
└─[D] Manipulate the /risk/composite response in transit
     └─ Tamper with JSON response before dashboard reads it  ──── mitigated by HMAC signing (Tree mitigation B above)
```

---

## 5. Residual Risks

The following risks are **not fully addressed** in the PoC and should be noted for production hardening:

1. **Cold-start / thin-baseline problem.** Enrolment requires only 3 events per layer. An attacker who observes the user during these first few interactions (e.g., shoulder-surfing at onboarding) can replay a reasonable approximation. Production systems should require 10–20 sessions of passive observation before the baseline is considered reliable.

2. **Mobile and touch adaptation.** All three layers assume desktop/keyboard input patterns (hover latency, key intervals, navigation entropy). On mobile, these signals have fundamentally different distributions (touch lag, virtual keyboard timing). The Isolation Forest models trained on desktop data will generate high false-positive rates on mobile — users will be incorrectly flagged. Separate mobile enrolment and separate model instances are required.

3. **Gradual model poisoning over time.** If the system implements continuous learning (updating baselines from accepted sessions), a patient attacker who scores Amber over many sessions can slowly drift the baseline toward their own rhythm. The PoC has a static baseline post-enrolment, which avoids this — but any online learning mechanism must include drift-rate limits and outlier rejection.

4. **Threshold gaming via prior knowledge.** The score thresholds (Green < 60, Red ≥ 85) and fusion weights (0.30/0.40/0.30) are constants in the PoC code. An attacker with access to the source code (e.g., a malicious insider, or if the repo is inadvertently public) can reverse-engineer the exact score they need to achieve on each layer. Mitigations: randomise thresholds per session within a small band, store weights server-side only, and treat them as secrets.

---

## 6. Compliance Note — RBI Data Localisation

PhantomGrid stores only **derived behavioural vectors** — inter-key timing intervals (in milliseconds), navigation entropy values, and hover latency measurements. No personally identifiable information (PII) is captured or persisted: the system records no biometric images, no keystrokes, no passwords, and no account numbers. The `user_id` field is an opaque internal identifier with no intrinsic PII value. Under the Reserve Bank of India's data localisation framework (RBI circular on Storage of Payment System Data, 2018) and the Digital Personal Data Protection Act 2023, anonymised derived metrics of this nature — which cannot be reverse-engineered into PII without the original session context — satisfy the requirement that payment data be stored exclusively on Indian-domiciled infrastructure. In production deployment, the `phantomgrid.db` SQLite file (or its cloud equivalent) must reside on servers physically located in India; no baseline vectors or session logs should be replicated to overseas infrastructure. This PoC assumes a single-region localhost deployment, which is compliant for hackathon evaluation purposes, and the architecture imposes no barriers to Indian-region cloud deployment (AWS ap-south-1, Azure centralindia, GCP asia-south1).
