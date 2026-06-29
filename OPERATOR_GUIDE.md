# PhantomGrid — Operator Guide (read this before presenting)

Everything you need to run, train, and present the whole system on your demo laptop.
All steps below are **verified working** on this machine.

---

## 1. The mental model — three pieces, one brain

PhantomGrid is **three separate things** that talk through one backend:

| Piece | What it is | Who it's for | File |
|-------|-----------|--------------|------|
| **Bank UI** | The NexaBank app a customer uses | the *customer* | `frontend/Nexa_bank_demoUI.html` |
| **Backend** | The risk brain (scores + decides) | runs invisibly | `backend/` (FastAPI) |
| **Analyst Dashboard** | Live security console | the *bank analyst* (you) | `dashboard/index.html` |

The Bank UI and the Dashboard are **two different browser tabs**. They are "integrated"
because they share the **same backend + database** — a payment in the Bank UI shows up on
the Dashboard within 2 seconds. That shared-backend link *is* the integration.

```
  Bank UI tab  ──POST /verify──►  BACKEND (:8000)  ──writes──►  SQLite
                                       ▲                           │
  Dashboard tab  ──GET /logs every 2s──┴───────────────────────────┘
```

---

## 2. One-time setup (already done, but if you move laptops)

```
pip install fastapi "uvicorn[standard]" scikit-learn sqlalchemy pydantic dtaidistance requests pytest
```

---

## 3. Start everything (3 terminals)

Open 3 terminals in `C:\Users\LENOVO\OneDrive\Desktop\PhantomGrid`.

**Terminal 1 — Backend (the brain):**
```
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
Wait for `Application startup complete`. ✅ Test: open http://127.0.0.1:8000/docs

**Terminal 2 — Analyst Dashboard:**
```
cd dashboard
python -m http.server 5599
```
Open → **http://localhost:5599**

**Terminal 3 — Bank UI:**
```
cd frontend
python -m http.server 5600
```
Open → **http://localhost:5600/Nexa_bank_demoUI.html**
*(you MUST type the filename — the folder has no index.html, so plain `:5600` shows a file list)*

> Put the **Dashboard** and **Bank UI** in two windows side by side. That side-by-side
> is your demo: act on the left (Bank UI), watch the right (Dashboard) react.

---

## 4. How to know it's all connected (the proof)

1. Backend up → http://127.0.0.1:8000/docs shows the Swagger page with `/enroll /verify /logs`.
2. Dashboard up → bottom status bar is **not** "⚠ API offline". It shows ALLOW/OTP/BLOCK.
3. **The integration proof:** run `python demo_attacker.py` in a terminal → within 2s a new
   **red BLOCK row** appears at the top of the Dashboard's session log, the gauge jumps to
   100, and the screen flashes red. If that happens, all three pieces are wired. ✅

---

## 5. Training Mode (enrolling YOUR behavior)

**What enrollment is:** the first 5 sessions teach the backend *your* normal behavior
(your PIN typing rhythm, your navigation). After 5, it locks your baseline and switches
to *scoring* mode. The Bank UI account is hard-coded to user **`arjun_4821`**.

### Step-by-step

1. **Reset to a clean slate** (so you train fresh):
   - Stop the backend (Ctrl+C in Terminal 1), delete `backend/phantomgrid.db`, restart it.
     (The backend recreates an empty database on startup.)
   - In the Bank UI browser tab, open DevTools console (F12) and run `localStorage.clear()`,
     then reload. *(Tip: an Incognito window starts clean every time.)*

2. **Open the Bank UI in training mode** — add `?enroll=true`:
   ```
   http://localhost:5600/Nexa_bank_demoUI.html?enroll=true
   ```
   You'll see a **blue banner at the top: "Baseline Training — Session 1 of 5"**. That banner
   is *where training is shown.*

3. **Do 5 full payments, the same natural way each time:**
   - Click **💸 Transfer** → pick a beneficiary → enter an amount → type your **6-digit PIN**
     at your *natural* rhythm → **Confirm & Pay**.
   - Each confirm = one training sample. The banner advances: *Session 2 of 5 … 5 of 5*.
   - Do it **8–10 times** if you can (after 5 the backend keeps refining via adaptive
     learning up to 20 — more reps = a more robust "you").

4. **Baseline complete:** after the 5th, you get an alert **"Enrollment Complete.
   Verification Mode Activated."** and the banner turns green. From now on every payment is
   **scored**, not stored.

5. **Confirm your baseline is good:** do one more normal payment → it should come back
   **ALLOW (green)** on the Dashboard. If it shows OTP/BLOCK, your reps were inconsistent —
   reset and train again, more evenly.

> ⚠ **Train on the exact laptop + keyboard you'll demo on.** Keystroke rhythm changes
> between keyboards — a baseline trained elsewhere will false-flag you.

---

## 6. Running the live demo (what happens, where to look)

You're watching the **Dashboard** (right window) while acting in the **Bank UI** (left).

**Legit session (you):** make a payment typing your normal PIN rhythm.
- Bank UI: ✅ "Payment Authorized".
- Dashboard: gauge low/green, a new **ALLOW** row, "WHY" panel says *all signals within baseline.*

**Attacker session:** on the *same* `arjun_4821` account, type the PIN with a **different
rhythm**, tap a couple of decoy buttons, hesitate on the amount.
- Bank UI: 🚨 "Transaction Blocked".
- Dashboard: gauge slams to ~100, **full-screen red flash + beep**, a **BLOCK** row, and the
  "WHY" panel names the reasons (*PIN rhythm does NOT match baseline*, etc.).

**The line that wins:** *"They have the correct PIN — and they still can't get in."*

> The Bank UI's little score bars inside the result pop-up are cosmetic (a known Person 1↔2
> wiring gap). **The Dashboard is the source of truth for the layer scores** — point there.

---

## 7. Dashboard interface tour (know every element)

| Element | Where | What it means |
|---------|-------|---------------|
| **LIVE ●** (top) | header | pulsing = dashboard is polling |
| **Composite gauge** | top-left | fused risk 0–100; green <60, amber 60–79, red ≥80 |
| **Decision word** | under gauge | ALLOW / OTP / BLOCK (from the backend) |
| **WHY THIS DECISION** | left, under gauge | per-layer human reasons — your explainability story |
| **Session Log** | center | last 10 sessions (GET /logs): time, user, L1/L2/L3, composite, decision badge |
| **L1 / L2 / L3 bars** | bottom strip | live layer scores — CognitiveTrap / IntentTrace / RhythmLock |
| **Status bar** | bottom | ALLOW/OTP/BLOCK message; flashes amber on OTP, red on BLOCK |
| **OTP toast** | top, on amber | "OTP RE-AUTH TRIGGERED" — the step-up moment |
| **Full-screen red flash** | on BLOCK | "⛔ SESSION BLOCKED" — the money shot |
| **Filter user** | bottom-right | optional: type a user_id to show only their rows |

## 8. Bank UI interface tour

| Element | What it is |
|---------|-----------|
| **Home / Transfer / Cards / Invest / Profile** | nav; **Transfer** is where the demo happens |
| **Decoy buttons** (Invest, Scan QR, etc.) | invisible traps — tapping them feeds Layer 1 |
| **Beneficiary list** | how long you hover/dwell feeds Layer 2 |
| **Amount field** | hesitation between digits feeds Layer 2 |
| **6-digit PIN pad** | inter-key timing feeds Layer 3 (RhythmLock) — the key signal |
| **Confirm & Pay** | sends the whole behavioral package to the backend |
| **Blue/green training banner** | only with `?enroll=true`; shows enrollment progress |
| **🎮 Demo button** | Person 1's manual demo shortcuts (optional) |

---

## 9. Backup scripts (your safety net — they cannot fail)

If live typing fumbles on stage, run these in a terminal (they use fresh accounts, no
enrollment dance, guaranteed result, and show up on the Dashboard):
```
python demo_attacker.py    # → BLOCK (dashboard goes red)
python demo_legit.py       # → ALLOW (dashboard green)
```

**Recommended demo strategy:** enroll your real rhythm once (impressive — "this is *my*
rhythm"), do the **legit** session live, and use **`demo_attacker.py`** as the reliable
attacker (or type a wrong rhythm live and keep the script ready as backup).

---

## 10. Reset between practice runs

| To reset… | Do this |
|-----------|---------|
| Browser enroll state | `localStorage.clear()` in console, or use a fresh Incognito window |
| A user's baseline | stop backend → delete `backend/phantomgrid.db` → restart |
| Just clear the log view | it auto-trims to the last 10; nothing to do |

---

## 11. Quick reference card

```
Backend    cd backend   && python -m uvicorn main:app --host 127.0.0.1 --port 8000
Dashboard  cd dashboard && python -m http.server 5599   →  http://localhost:5599
Bank UI    cd frontend  && python -m http.server 5600   →  http://localhost:5600/Nexa_bank_demoUI.html?enroll=true
Tests      pytest tests/ -v
Backup     python demo_attacker.py   |   python demo_legit.py
Decision   ALLOW <60   ·   OTP 60–79   ·   BLOCK ≥80
```
```
If presenting remotely / different network: set the backend host in BOTH
config.py (BASE_URL) and dashboard/index.html (the BASE constant), and capture.js
points at localhost:8000 by default.
```
