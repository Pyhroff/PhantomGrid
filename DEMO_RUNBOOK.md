# PhantomGrid — Demo Day Runbook

A tight, repeatable script for the live demo + a backup that cannot fail.
Keep this open on a second screen / phone during the demo.

---

## T-30 min — Setup (do this before judges arrive)

1. **Start the backend** (from the project root):
   ```
   cd backend
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```
   Wait for `Application startup complete`. Leave it running.

2. **Serve + open the dashboard** (new terminal):
   ```
   cd dashboard
   python -m http.server 5599
   ```
   Open `http://localhost:5599` in the browser. Status bar should read **ALLOW**
   (or "API offline" until the first session — that's fine).

3. **Pre-enroll YOUR real rhythm** on THIS laptop (keystroke rhythm is device-specific):
   open the bank UI in enroll mode, do **8–10 legit sessions** typing your PIN
   naturally under `user_id = demo_user`. Verify once → must be green/ALLOW.

4. **Smoke-test the backups** once:
   ```
   python demo_legit.py      # → ALLOW
   python demo_attacker.py   # → BLOCK (dashboard flashes red)
   ```

> If `BASE_URL` is an ngrok/Railway host, set it in **`config.py`** AND in the
> dashboard's `BASE` constant before step 2.

---

## The 4-minute demo

| # | You do | You say |
|---|--------|---------|
| 1 | Show the dashboard | "This is the bank's analyst view. It watches every live session in real time — three behavioral layers fused into one risk score." |
| 2 | Run a **legit** session (your portal, or `python demo_legit.py`) | "Genuine customer. Navigation is habitual, PIN rhythm matches. Composite ~2 — **ALLOW**. Zero friction — they never even know we're here." |
| 3 | Run the **attacker** (`python demo_attacker.py`) | "Same account, stolen credentials. They tap decoys, they hesitate — and here's the key: **they type the correct PIN, but in their own rhythm.**" |
| 4 | Gauge slams to 100, screen flashes red | "Composite 100 — **BLOCK**. Look at *why*: RhythmLock says the PIN rhythm does NOT match. The stolen PIN wasn't enough." |
| 5 | Point at the **WHY THIS DECISION** panel | "Every block is explainable, per-layer — that's what an RBI auditor needs." |
| 6 | (Optional) run `pytest tests/ -v` | "Eight integration tests, green, against the live backend." |

**The line that wins the room (step 3):**
> *"They have the correct PIN — and they still can't get in."*

---

## Backup plan (if live input fumbles)

Just run the scripts — they enroll a fresh account and force the outcome:
```
python demo_attacker.py    # guaranteed BLOCK, dashboard goes red
python demo_legit.py       # guaranteed ALLOW
```
Each prints the layer scores + decision and writes a row the dashboard shows within 2s.

---

## Full verified sequence (the "advanced" demo — all 5 stages tested green)

Run these in order with the dashboard visible. Last full dry-run: **all 5 passed.**

| # | Command | Expected | What to say |
|---|---------|----------|-------------|
| 1 | `python demo_legit.py` | `DECISION → ALLOW` | "Genuine user — composite ~2, zero friction." |
| 2 | `python demo_attacker.py` | `DECISION → BLOCK` | "Correct PIN, wrong rhythm → blocked." (red flash) |
| 3 | `python demo_replay.py` | `replay_detected = True → BLOCK` | "Sniffed session replayed verbatim → blocked. Behaviour can't be copy-pasted." |
| 4 | `python verify_audit.py --tamper` | `VALID → TAMPERED ✗ → VALID` | "Edit any DB record → the hash chain catches exactly which one." |
| 5 | `pytest tests/ -v` | `8 passed` | "Eight integration tests, green, against the live backend." |

Throughout, the dashboard's **🛡 AUDIT VERIFIED ✓** badge and **Baseline maturity** line update live.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Dashboard says "API offline" | Backend not running, or `BASE` in dashboard ≠ backend host. |
| Attacker shows OTP not BLOCK | The account's baseline was polluted by many prior legit runs — use a **fresh `user_id`** (the scripts already do this). |
| Legit shows OTP/BLOCK | Your enrollment reps were inconsistent — re-enroll more evenly on the demo machine. |
| `ModuleNotFoundError` | `pip install fastapi "uvicorn[standard]" scikit-learn sqlalchemy pydantic dtaidistance requests` |
| Unicode error in console | Already handled — scripts force UTF-8 output. |

---

## What to have ready for judge Q&A
- **`DEMO_PREP.md`** — ML explained, RBI compliance, full judge Q&A bank.
- **`threat_model/THREAT_MODEL.md`** — STRIDE table, DFD, risk matrix, attack trees.
- **`architecture.svg`** — the one-glance system diagram.
- **`CHANGELOG_RISK_ENGINE.md`** — if asked how scoring works / why continuous.
