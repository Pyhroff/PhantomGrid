# PhantomGrid — Judge Q&A Cheat Sheet
**Keep this open during the demo. Memorize the bold punchlines.**

---

## Technology

**"Why not just use MFA?"**
> MFA authenticates *who you are once* at login. PhantomGrid authenticates *how you behave continuously* throughout the session. An attacker with stolen credentials AND the OTP still can't fake the victim's typing rhythm.

**"Why ML — not rules?"**
> Rules like "flag if hover > 300ms" fail because 65-year-olds and 22-year-olds have completely different baselines. **Isolation Forest learns each user's personal norm** — it flags deviation from YOUR average, not a global one.

**"Isn't 5 keystroke intervals too little?"**
> For identification across millions — yes. For **verification** (is this my enrolled user?), 5 is enough. People type their own PIN daily; the rhythm is stable. DTW FRR under 5% at n=5, same-device.

**"What if the legit user changes — stress, new phone?"**
> `contamination=0.10` covers ~10% natural variance. Plus adaptive learning: every ALLOW session is appended to the baseline (sliding window of 20), so the model slowly drifts with the user.

**"Is the weighted average rigorous enough for fusion?"**
> The fusion math is simple. The rigor is in what flows into it — IF anomaly scores and DTW distances from trained per-user models, not raw signal values. L2 weight is highest (0.40) because nav entropy + beneficiary dwell are the strongest fraud signals from the payment-fraud literature.

---

## Security

**"Can't the attacker just replay a captured session?"**
> **No — we built this.** Every `/verify` payload is SHA-256 signed. An exact duplicate within 5 minutes is detected by `services/audit.py::is_replay()` → forced BLOCK, `replay_detected:true`. Run `python demo_replay.py` to show it live.

**"Can an attacker poison the enrollment baseline?"**
> `/enroll` must be called under an authenticated session — enrollment without a valid auth token is an Elevation of Privilege attack, flagged in the threat model. Clear production fix: tie `/enroll` to the bank's login JWT. Known PoC limitation, not a design flaw.

**"How do you prevent log tampering — an insider could just edit the DB?"**
> **We hash-chained the audit log.** Each `session_logs` row has a `row_hash` (SHA-256 of that row) and `prev_hash` (hash of the prior row). Edit any row → `GET /audit/verify` immediately flags exactly which one. Dashboard shows `🛡 AUDIT VERIFIED ✓`. Run `python verify_audit.py --tamper` to demo it.

**"What's your FPR/detection rate?"**
> Measured on 200 synthetic sessions: **96.7% detection rate, 0.0% FPR, AUC 1.00**. Run `benchmark.py` or open `benchmark_report.html`. These are PoC numbers on controlled data — production numbers require a live cohort study.

**"What if the attacker knows your fusion weights?"**
> Knowing weights doesn't help without also fooling all three independent behavioral models simultaneously — each uses a different algorithm and signal domain. Even with weights known, you still need to mimic L1 decoy avoidance, L2 navigation entropy, AND L3 PIN rhythm. See the attack tree in `threat_model/THREAT_MODEL.md`.

---

## Architecture / Demo

**"Why SQLite?"**
> Deliberate PoC scope (4-5 day hackathon). The schema is standard SQL — one connection-string swap moves it to PostgreSQL. Zero infra dependency = reliable demo.

**"Why vanilla JS, no React?"**
> No build step, no npm, works in any browser by opening `index.html`. For production, the API contract in `INTEGRATION_NOTES.md` is framework-agnostic.

**"How does the dashboard get live data?"**
> Polls `GET /logs` every 2 seconds. Latest row drives the gauge + decision badge; all rows fill the session table. Offline? Dashboard shows "API offline" and retries — it never crashes.

---

## RBI / Compliance

**"Is keystroke timing biometric data under DPDP 2023?"**
> Behavioral data, not physiological biometric. DPDP defines biometrics as physiological/biological data used for unique identification — fingerprints, iris scans. Keystroke timing is a derived behavioral metric used for session-level verification, not identification. Comparable to storing transaction aggregates, not transactions. Recommend legal counsel for production deployment.

**"What about data localisation?"**
> PoC runs localhost. Production: deploy on `aws ap-south-1 Mumbai` or `azure centralindia`. No `user_profiles` or `session_logs` rows ever leave the Indian region. Documented in §7 of `DEMO_PREP.md`.

---

## The one line that wins the room
> **"They have the correct PIN — and they still can't get in."**
