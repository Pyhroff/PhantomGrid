# PhantomGrid — Integration Notes

**For:** Person 1 (Frontend) and Person 2 (Backend)  
**From:** Person 3 (Analyst Dashboard + Tests)  
**Date:** June 2026  

---

## Endpoints the Dashboard Consumes

### Already implemented (Person 2)

| Method | Path | Used by |
|--------|------|---------|
| GET | `/risk/composite?user_id={uid}` | Dashboard — polled every 2 s for live composite score + breakdown |

**Expected response shape for `GET /risk/composite`:**
```json
{
  "composite_score": 42.5,
  "decision": "green",
  "breakdown": {
    "layer1": 38.0,
    "layer2": 45.0,
    "layer3": 41.0
  }
}
```
The dashboard reads `breakdown.layer1 / layer2 / layer3` for the three mini score bars. If your response uses different keys (e.g. `l1`, `l2`, `l3`), let Person 3 know and the dashboard will be updated.

---

## Missing Endpoint — Person 2 Must Implement

```
GET /sessions?user_id={uid}&limit={n}
```

**Purpose:** Populate the "Session Log — Last 10" table in the dashboard.

**Expected response** (JSON array, most-recent first):
```json
[
  {
    "session_id": "abc123",
    "timestamp": "2026-06-15T14:32:01.000Z",
    "user_id": "demo_user",
    "layer1_score": 38.0,
    "layer2_score": 45.0,
    "layer3_score": 41.0,
    "composite_score": 42.5,
    "decision": "green"
  }
]
```

**Notes:**
- `timestamp` should be ISO 8601 (the dashboard passes it to `new Date()`)
- Return at most `limit` rows ordered by `timestamp DESC`
- Source: `session_logs` table — all columns are already being written there by `/risk/composite`
- If this endpoint is not yet available, the dashboard silently keeps the placeholder row and retries every 2 s — no crash

---

## SQLite DB Filename

The integration tests connect directly to SQLite to verify that session rows are persisted after `/risk/composite` calls.

**Tests assume:** `phantomgrid.db` at the **project root** (same directory where `pytest` is run from).

Please confirm this is the actual filename and path Person 2's backend uses. If it differs, update `tests/test_integration.py` line:
```python
conn = sqlite3.connect("phantomgrid.db")
```

---

## CORS — Required FastAPI Config

The analyst dashboard is opened as a local `file://` URL (or may be served on a different port). Browsers block cross-origin requests by default, so the FastAPI backend **must** add CORS middleware or the dashboard will silently fail to poll.

Add this to `main.py` (Person 2):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Without this, every `fetch()` from the dashboard returns a CORS error and the status bar shows "⚠ API offline".

---

## Running the Tests

```bash
# from project root (where phantomgrid.db lives)
pytest tests/ -v
```

Tests auto-skip if `http://localhost:8000/docs` is unreachable. Enrolment of `test_user` happens once via a session-scoped fixture in `conftest.py` — no manual setup needed.

---

## Amber — OTP Re-Auth Overlay (Person 1 Must Implement)

When the composite score hits Amber (60–84), the proposal requires a **silent OTP re-authentication overlay** on the banking portal — no session disruption, just a prompt before the transaction proceeds.

**What the analyst dashboard already does (Person 3):**
- Shows an amber toast banner: "OTP RE-AUTH TRIGGERED"
- Flashes the status bar amber
- Status reads "AMBER — OTP re-auth triggered"

**What Person 1's banking frontend must do:**

Poll `GET /risk/composite?user_id={uid}` every 2s (same as the dashboard). When `decision === "amber"`:

1. Intercept the transaction submit button — disable it
2. Show an OTP modal overlay on the banking page:

```html
<!-- Drop this modal into your banking portal HTML -->
<div id="otp-overlay" style="display:none; position:fixed; inset:0;
     background:#00000099; z-index:9999; display:flex;
     align-items:center; justify-content:center;">
  <div style="background:#1a1a2e; border:1px solid #d97706;
       border-radius:8px; padding:32px; text-align:center; max-width:320px;">
    <p style="color:#fbbf24; font-weight:700; margin-bottom:8px;">
      Security Verification Required
    </p>
    <p style="color:#aaa; font-size:13px; margin-bottom:20px;">
      Unusual activity detected. Please verify with OTP.
    </p>
    <input id="otp-input" type="text" maxlength="6"
           placeholder="Enter OTP"
           style="width:100%; padding:10px; border-radius:4px;
                  border:1px solid #444; background:#0d1117;
                  color:#fff; text-align:center; font-size:18px;
                  letter-spacing:0.3em;" />
    <button onclick="submitOtp()"
            style="margin-top:12px; width:100%; padding:10px;
                   background:#d97706; border:none; border-radius:4px;
                   color:#000; font-weight:700; cursor:pointer;">
      Verify
    </button>
  </div>
</div>
```

3. On successful OTP verify — re-enable the transaction button, hide overlay, proceed
4. On failure — block transaction, call `POST /risk/composite` to log a Red session

**Trigger logic (add to your existing polling):**
```js
// Person 1 — add this to your polling loop
if (data.decision === 'amber' && !otpOverlayShown) {
  document.getElementById('otp-overlay').style.display = 'flex';
  document.getElementById('submit-btn').disabled = true;
  otpOverlayShown = true;
}
if (data.decision === 'green') {
  otpOverlayShown = false; // reset if session recovers
}
```

**Note:** The OTP itself is out of PhantomGrid's scope — it hooks into the bank's existing OTP service. PhantomGrid just triggers the challenge; the bank's auth infra handles delivery and verification.

---

## Checklist

| Item | Owner | Status |
|------|-------|--------|
| `GET /risk/composite?user_id=X` returns `composite_score + decision + breakdown` | Person 2 | — |
| `GET /sessions?user_id=X&limit=N` implemented | Person 2 | **MISSING** |
| CORS middleware added to FastAPI | Person 2 | — |
| SQLite DB filename confirmed as `phantomgrid.db` at project root | Person 2 | — |
| Dashboard opens at `dashboard/index.html?user_id=demo_user` | Person 3 | Done |
| Amber toast + flash in analyst dashboard | Person 3 | Done |
| Amber OTP overlay on banking portal | Person 1 | **MISSING** |
| Integration tests pass against live backend | Person 3 | Pending backend |
