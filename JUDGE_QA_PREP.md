# PhantomGrid — Judge Q&A Preparation
**CBI Hackathon 2026 Phase II | Team ZeroIntent | IIIT Kottayam**

Tags: `[EASY]` expected every time | `[MED]` technical depth required | `[HARD]` know this cold

---

## CATEGORY 1 — Problem & Motivation

**Q: Why focus on PSBs specifically?**
`[EASY]`
PSBs hold the accounts of India's mass-market banking population — pensioners, rural account holders, low-digital-literacy users who are disproportionately targeted by social engineering and credential theft. RBI reported ₹7,400 crore in digital fraud losses in FY2023, majority from PSBs. Private banks have more resources for custom fraud infra; PSBs need a deployable passive layer.

**Q: Isn't this a solved problem? Banks already have fraud detection.**
`[MED]`
Existing solutions operate at the transaction layer — they flag a ₹5L transfer if the account usually transfers ₹500. PhantomGrid operates at the session layer — it asks "is this the same human who enrolled?" before the transaction amount matters. Rule-based velocity checks, device fingerprinting, and IP geolocation all fail against an attacker using the victim's device with correct credentials. Behavioural biometrics is the only control that remains effective in that scenario.

**Q: What are the three specific attack vectors you're defending against?**
`[EASY]`
1. Credential phishing — attacker authenticates with stolen username + password + OTP
2. SIM-swap fraud — attacker receives victim's OTP on a cloned SIM
3. Session hijacking — attacker injects into an already-authenticated browser session

In all three, the attacker passes every existing control. PhantomGrid catches them because their behavioural profile is different from the enrolled user's.

---

## CATEGORY 2 — System Architecture

**Q: Walk me through the architecture end to end.**
`[EASY]`
Three tiers: (1) Browser — `capture.js` hooks into DOM events silently and sends a compact JSON payload per transaction. (2) Backend — FastAPI + Python receives the payload, runs it through three IsolationForest/DTW models, fuses the scores, writes to SQLite, returns composite risk. (3) Dashboard — analyst-facing real-time monitor polling `/risk/composite` every 2 seconds.

**Q: Why FastAPI over Flask or Django?**
`[MED]`
FastAPI gives us automatic Pydantic v2 validation on every request body, async support for concurrent scoring requests, and auto-generated Swagger docs that judges can use to test the API without any setup. Flask would have required manual validation boilerplate; Django is overkill for a pure API service.

**Q: Why SQLite and not PostgreSQL?**
`[EASY]`
SQLite is the right choice for a hackathon POC — zero config, ships with Python, deployable on Railway with one command. The ORM (SQLAlchemy 2.0) is database-agnostic. Switching to PostgreSQL is a one-line connection string change. All schema, query, and hash-chain logic is production-ready.

**Q: How does the enrollment flow work?**
`[MED]`
The user completes 5 normal transactions. `capture.js` posts each one to `/enroll` (or layer-specific `/enroll/layer1`, `/enroll/layer2`, `/enroll/layer3`). The backend accumulates vectors in `UserProfile.layer1_vectors`, `layer2_vectors`, `pin_vectors` as JSON arrays. The `/maturity` endpoint returns enrollment confidence. From session 6 onward, every transaction hits `/risk/composite` for live scoring.

**Q: What is the `/maturity` endpoint?**
`[MED]`
It exposes baseline confidence as a percentage — how many enrollment samples have been collected out of the required minimum. The bank's operator dashboard uses this to gate enforcement: PhantomGrid can run in shadow mode (collect but don't block) until maturity is 100%, then switch to enforcement. This prevents false positives during the enrollment phase.

**Q: Why is `allow_origins=["*"]` in your CORS config?**
`[HARD]`
In the POC, we allow all origins so the bank UI, dashboard, and Swagger can all talk to the backend without origin whitelist management. In production, this would be locked to the bank's specific domain list. CORS is a browser-level control — it doesn't protect server-to-server calls — so the real security is in session token validation, not CORS headers.

---

## CATEGORY 3 — Machine Learning

**Q: Why IsolationForest and not a neural network?**
`[HARD]`
Neural networks need hundreds of samples to generalise. We have 5 enrollment sessions — 5 feature vectors per layer per user. IsolationForest is a tree-based anomaly detector that works on small samples with no distributional assumptions. It isolates anomalies by randomly partitioning the feature space — outliers require fewer splits to isolate. It's the only algorithm that reliably works at n=5 without overfitting.

**Q: Why not LSTM or a recurrent model for sequence data?**
`[HARD]`
LSTM requires sequence length and training volume we don't have at enrollment. DTW (Dynamic Time Warping) is mathematically designed for sequence comparison with elastic time alignment — it measures how similar two time-series are even if one is slightly faster or slower. For 5-interval PIN rhythm comparison, DTW is more appropriate and more interpretable than a trained RNN.

**Q: What is contamination=0.10 and why that value?**
`[MED]`
It tells IsolationForest to expect ~10% of its own training data to be anomalous. This accounts for natural day-to-day variance — a user who is stressed, tired, or using a slightly different device. If we set it to 0, the model becomes hypersensitive and flags minor legitimate variation. 0.10 gives a tolerance band while still catching attackers whose profiles are significantly different.

**Q: Why is L2 weighted highest at 0.40 in the fusion?**
`[MED]`
L2 (IntentTrace) captures transaction intent — beneficiary dwell time and amount inter-key interval. These signals are the hardest to fake and most directly correlated with fraud intent. An attacker rushing through the beneficiary field or typing amounts differently from the enrolled user is a stronger fraud signal than hover hesitation (L1) or PIN rhythm (L3) alone.

**Q: What is Dynamic Time Warping?**
`[MED]`
DTW is an algorithm for measuring similarity between two time-series sequences that may vary in speed. It finds the optimal alignment between the sequences by stretching or compressing along the time axis. For PIN rhythm: it compares the attacker's 5 inter-keystroke intervals against the enrolled baseline, tolerating minor timing variation but flagging significant rhythm divergence. Distance 0 = identical rhythm. Distance ≥ 180 = 100 risk score.

**Q: What is normalized deviation and why did you add it?**
`[HARD]`
The original IsolationForest bucketed scores into 4 fixed values (10/40/70/95). The problem: IsolationForest's `decision_function` saturates on tiny baselines — every anomaly collapsed to the same value (~-0.01), so L2 could never exceed 70 regardless of how anomalous the session was. We added a continuous deviation magnitude that measures how far the current point sits from the baseline mean in z-score space. This makes scores ramp smoothly 0–100 instead of snapping to fixed buckets.

```python
deviation = sqrt( sum( ((x - mean) / max(std, floor)) ^ 2 ) / n_features )
```

**Q: How does the scoring work when a user has fewer than 10 enrollment samples?**
`[HARD]`
Below 10 samples, IsolationForest is unreliable — it can misclassify extreme outliers as inliers. We skip the IF gate entirely for thin baselines and use pure normalized deviation:
`risk = min(100, deviation × 30)`. This is deterministic, monotonic, and correct for small n. Once the baseline grows past 10 samples, the IF gate re-engages.

**Q: What is adaptive learning and how does it work?**
`[MED]`
After every ALLOW decision (composite < 60), the session's behavioural vectors are appended to the user's baseline. The baseline is capped at a sliding window of 20 samples — the oldest sample is dropped when the 21st is added. This allows the model to slowly adapt to legitimate behavioural drift (ageing, device change, habit change) without requiring re-enrollment.

---

## CATEGORY 4 — Security

**Q: How does replay attack defence work?**
`[MED]`
Every behavioural payload is SHA-256 hashed over all 6 behavioural fields in canonical sorted-key JSON. The hash is stored in memory with a timestamp. If the same hash appears within 5 minutes, the request is rejected as a replay. A genuine session is never byte-identical twice — rhythm naturally varies.

**Q: What is the hash chain in the audit log?**
`[HARD]`
Every `session_logs` row includes a SHA-256 hash of itself plus the previous row's hash — a blockchain-style chain. Any edit to any field in any historical record breaks the chain from that point forward. Auditors (or RBI inspectors) can verify chain integrity by recomputing hashes. This satisfies PSB audit trail requirements for fraud investigation.

```
row_hash = SHA-256( prev_hash | session_id | user_id | L1 | L2 | L3 | composite | decision | timestamp )
```

**Q: What stops an attacker from poisoning the ML model?**
`[HARD]`
Only ALLOW sessions (composite < 60) are appended to the baseline. A blocked or OTP-triggered session is never learned from. An attacker who cannot get below 60 can never modify the baseline. This is a deliberate design choice — adaptive learning is gated on the decision outcome, not on the session completion.

**Q: What are your STRIDE threat mitigations?**
`[HARD]`
- Spoofing: session token binding + SHA-256 replay detection (5-min window)
- Tampering: HMAC-signed API responses (production); HTTPS at minimum in POC
- Repudiation: tamper-evident hash chain on all session logs
- Information Disclosure: encrypt SQLite at rest with SQLCipher; per-user key derivation from HSM in production
- Denial of Service: rate limiting per `user_id` and IP (FastAPI `slowapi` middleware)
- Elevation of Privilege: enrollment endpoints require authenticated session token proving caller is the claimed `user_id`

**Q: Is CORS `allow_origins=["*"]` a security vulnerability?**
`[MED]`
In the POC context, no — CORS is a browser-level same-origin policy enforcement mechanism, not a server-side authentication control. An attacker making direct API calls (curl, Postman) is unaffected by CORS headers regardless of the setting. The actual security control is session token validation. In production, CORS would be locked to the bank's registered domains.

**Q: What is the brute-force resistance of Layer 3?**
`[HARD]`
5 intervals, each in the range ~50–400ms, with DTW tolerance roughly ±15ms. The search space is approximately (350/15)^5 ≈ 5×10^10 combinations. Each requires a live API call. With rate limiting at 10 requests/minute/user, exhaustive brute force would take ~950 years.

---

## CATEGORY 5 — Data & Privacy

**Q: Is this GDPR/DPDP Act compliant?**
`[MED]`
PhantomGrid stores only derived behavioural vectors — inter-keystroke intervals in milliseconds, navigation entropy values, hover latency measurements. No keystrokes, no raw input, no PII. The `user_id` is an opaque internal identifier. Under the Digital Personal Data Protection Act 2023, anonymised derived metrics that cannot be reverse-engineered into PII satisfy the data minimisation principle. A full DPIA would be required for production deployment.

**Q: Does this comply with RBI data localisation?**
`[HARD]`
Yes. RBI's 2018 circular mandates storage of payment system data exclusively on Indian-domiciled infrastructure. PhantomGrid stores only derived behavioural vectors — no payment account numbers, no transaction amounts, no PII. These anonymised metrics satisfy the data localisation requirement when the server infrastructure is India-region (AWS ap-south-1, Azure centralindia, GCP asia-south1).

**Q: What data is actually stored in the database?**
`[MED]`
Two tables: `user_profiles` — stores per-user enrollment baseline vectors (L1 feature arrays, L2 feature arrays, L3 PIN interval arrays) as JSON blobs. `session_logs` — stores per-transaction risk scores (L1, L2, L3, composite), decision, timestamp, and hash chain fields (`row_hash`, `prev_hash`). No raw keystrokes, no passwords, no account numbers.

**Q: Can the PIN rhythm vectors be used to reconstruct the user's PIN?**
`[HARD]`
No. Layer 3 stores inter-keystroke timing intervals in milliseconds — the time between keypresses, not which key was pressed. The sequence [118, 92, 107, 85, 99] tells you nothing about whether the PIN is 1234 or 9876. Timing cannot be reverse-engineered into key identity.

---

## CATEGORY 6 — Scalability & Production

**Q: How does this scale to millions of PSB users?**
`[HARD]`
Each model is tiny — a 5–20 sample IsolationForest. Inference is under 5ms per request. The scoring layer is stateless — it reads the baseline from DB, scores, and returns. This means horizontal scaling behind a load balancer with no shared state at the compute layer. Production DB would be PostgreSQL with per-user baseline in Redis for sub-millisecond lookup. The ML inference is CPU-only — no GPU required.

**Q: What's the latency impact on the user's banking transaction?**
`[EASY]`
Less than 5ms for ML inference on the backend. The total round-trip (browser to Railway and back) adds ~50–100ms network latency on top, but this runs in parallel with the bank's existing transaction processing — it's not on the critical path. The user sees no additional wait time.

**Q: How would you deploy this in a real PSB?**
`[MED]`
Integration pattern: PhantomGrid runs as a sidecar microservice alongside the bank's existing transaction API. The bank's frontend adds `capture.js` to the banking portal. On every transaction submit, the browser posts to both the bank API (the actual transaction) and PhantomGrid (the behavioural scoring). If PhantomGrid returns BLOCK or OTP, the bank's transaction handler checks the signal before executing the transfer. No changes to the bank's core system are required.

**Q: What about mobile banking apps?**
`[HARD]`
The current POC targets web banking on desktop. `capture.js` hooks into browser mouse and keyboard events. For mobile, the equivalent is a native SDK capturing touchstart/touchend timing, swipe velocity, tap pressure, and virtual keyboard inter-key intervals. The ML backend is completely signal-agnostic — it takes numerical vectors regardless of how they were captured. Mobile is the next engineering milestone, not an architectural blocker.

---

## CATEGORY 7 — Limitations & Honest Answers

**Q: Your benchmark is synthetic. What does it actually prove?**
`[HARD]`
It validates that the scoring engine correctly separates two distinct populations — legitimate users and attackers. It does not prove real-world generalisability. The 300 sessions (150 legit + 150 attacker) were generated across a difficulty gradient including sophisticated mimics. The 7 false negatives represent cases where the attacker partially replicated the victim's rhythm. No synthetic benchmark replaces a field pilot with consented users. We document this honestly in `benchmark_results.md`.

**Q: Is the user vulnerable during enrollment?**
`[MED]`
Yes — enrollment is shadow mode. The system collects but doesn't enforce for the first 5 sessions. The bank should keep existing MFA active during enrollment and switch to PhantomGrid enforcement only once the `/maturity` endpoint confirms 100% baseline confidence. This is standard practice for all behavioural biometric systems — you cannot verify identity before having a reference.

**Q: What if the legitimate user changes — injury, stress, new device?**
`[MED]`
Two mechanisms handle this: (1) `contamination=0.10` tolerates ~10% natural variance per session. (2) Adaptive learning absorbs gradual drift by updating the baseline with each ALLOW session (sliding window 20). Sudden large changes — broken finger, extreme stress — could trigger an OTP prompt. That is correct behaviour: the OTP is completed, the session becomes ALLOW, and the new behavioural sample updates the baseline. Re-enrollment is the last resort.

**Q: What about the 7 false negatives in your benchmark?**
`[MED]`
They represent sophisticated mimics who partially replicated the victim's rhythm and navigation patterns. Mitigations for production: (1) device binding — even if rhythm is faked, the device signature must match; (2) increase sliding window to 30+ for high-risk accounts; (3) add a 4th signal layer (mouse dynamics or scrolling patterns) for high-value transactions. 95.3% is the floor for the current 3-layer implementation, not the ceiling.

**Q: Can the system be fooled by someone who watches the victim type?**
`[HARD]`
Partially. A sophisticated attacker observing the victim can approximate their rhythm but cannot precisely replicate it — motor memory is deeply personal and has millisecond-level variance invisible to observers. The attack tree in our threat model shows that even with approximate rhythm knowledge, the attacker must also pass L1 (decoy interaction patterns) and L2 (beneficiary dwell behaviour) simultaneously. All three layers must be faked to achieve a green composite score.

**Q: The fusion weights (0.30/0.40/0.30) are hardcoded. Is that a security risk?**
`[HARD]`
Yes — a knowledgeable attacker who reads the source code could optimise their behaviour to exploit the weight distribution. For example: score perfectly on L1 and L2, sacrifice L3. Production mitigations: store weights server-side only, add per-session randomisation within a small band (±5%), treat thresholds as secrets. In the POC, this is documented as a residual risk in the threat model.

---

## CATEGORY 8 — Demo-Specific Questions

**Q: Why does the bank UI show decoy buttons?**
`[EASY]`
They are the Layer 1 CognitiveTrap signals. A legitimate user who has used this banking interface before ignores the decoy buttons instinctively — they know where the "Pay" button is. An attacker exploring an unfamiliar interface tends to hover over or tap the decoys. `capture.js` counts these interactions silently and includes them in the L1 payload.

**Q: What are the green/amber/red thresholds?**
`[EASY]`
Composite score below 60 → ALLOW (green, no friction). 60–79 → OTP step-up (amber, existing 2FA prompt). 80 and above → BLOCK (red, session terminated). The OTP range means suspicious sessions get a second factor rather than a hard block — important for avoiding false-positive customer experience failures.

**Q: What is `demo_user` and how is it seeded?**
`[MED]`
`demo_user` is pre-enrolled at startup via `_seed_user()` in `main.py` using 5 synthetic legitimate samples. This allows immediate demo without going through the 5-session enrollment flow live. The baseline vectors approximate a real legitimate user's behavioural signature. `arjun_4821` is the interactive demo user who must be enrolled via the bank UI with real typing.

**Q: What happens if I call `/risk/composite` before enrollment?**
`[MED]`
The endpoint returns a 404 with `"User not enrolled"`. Enforcement requires a complete baseline. This prevents the system from scoring zero-data sessions, which would produce meaningless risk values.

---

## CATEGORY 9 — Business & Impact

**Q: What is the ROI for a PSB deploying this?**
`[EASY]`
₹7,400 crore total FY2023 digital fraud. At 95.3% detection rate: ~₹7,050 crore in fraud that would have been blocked before funds moved. Integration cost is a `<script>` tag in the existing banking portal and a sidecar microservice. No hardware, no user training, no app installation. ROI is immediate.

**Q: How is this different from what PSBs already have?**
`[MED]`
Existing PSB controls: password + OTP at login, transaction velocity rules (flag if transfer > ₹X), device fingerprinting (flag if new device), IP geolocation. All of these operate at login or at the transaction value level. None of them operate on the behavioural signature of the session occupant. PhantomGrid is the only control that asks "is this the same human?" at the transaction moment.

**Q: What's the user experience impact?**
`[EASY]`
Zero for legitimate users. `capture.js` is completely passive — users see nothing. The OTP prompt on amber scores is indistinguishable from a standard 2FA prompt. 0.0% false positive rate in our benchmark means no legitimate user is incorrectly challenged. Only attackers experience friction.

**Q: Who are your competitors?**
`[MED]`
BioCatch and BehavioSec are the commercial leaders in behavioural biometrics — both used by major US and European banks. Neither is deployed at Indian PSBs at scale due to cost and integration complexity. Our approach is designed for low-cost, low-friction deployment: no proprietary SDK, no cloud dependency (Railway is replaceable), no changes to the bank's core systems. The addressable gap is specifically India's PSB sector.

---

## CATEGORY 10 — Future Scope

**Q: What's the roadmap after this POC?**
`[MED]`
Three phases: (1) Field pilot — 500 consented users at one PSB branch, measure real FPR and FNR, tune thresholds against real behavioural data. (2) Mobile SDK — native iOS/Android capture layer feeding the same backend ML pipeline. (3) Multi-bank federation — anonymised threat signal sharing across PSBs so an attacker pattern seen at SBI is flagged at PNB before they attempt it.

**Q: What would you add with more time?**
`[MED]`
Layer 4: scrolling velocity and mouse pressure dynamics — adds a continuous passive signal between keypress events. Per-device calibration: separate baseline instances per device so a user's desktop and mobile baselines don't cross-contaminate. Explainability layer: when a session is blocked, the analyst dashboard should show which layer triggered and why, not just the composite score.

**Q: How would you handle multi-device users?**
`[HARD]`
Maintain separate baseline profiles per device fingerprint under the same `user_id`. The enrollment flow detects the device signature (browser + OS + screen resolution hash) and creates or retrieves the appropriate baseline. A user's desktop profile and mobile profile are scored independently before fusion. Cross-device authentication (user on new device) reverts to shadow mode for 5 sessions on that device.

---

## CATEGORY 11 — Team & Process

**Q: How did you divide the work?**
`[EASY]`
Madapati Jyoti Radithya: NexaBank portal UI, `capture.js` signal capture layer. Kontheti Sai Akhilesh: FastAPI backend, ML engine, Railway deployment. Praising Y Harris Ratnam: analyst dashboard, integration test suite, STRIDE threat model, technical documentation.

**Q: What was the hardest technical problem you solved?**
`[MED]`
The continuous scoring problem. The original IsolationForest returned 4 fixed values — scores never reflected how anomalous a session actually was. Layer 2 was capped at 70 because `decision_function` barely went negative on small baselines. We built a normalized deviation magnitude layer on top of IsolationForest that makes scores ramp smoothly 0–100, correctly representing both mild and extreme anomalies.

**Q: What didn't work as expected?**
`[HARD]`
Layer 2 initially couldn't exceed 70 due to IsolationForest saturation on the tiny per-user baseline. The DTW Layer 3 was originally bucketed into 4 fixed scores, throwing away the continuous distance information. Both were discovered during the benchmark run and fixed by rebuilding `services/scoring.py` with continuous scoring helpers. The benchmark results you see reflect the fixed engine, not the original one.

---

*Keep this open during the presentation. Know the HARD ones cold — judges at a banking hackathon will probe security and scalability hardest.*
