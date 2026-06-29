# PhantomGrid — Test Credentials

**CBI Hackathon 2026 | Team ZeroIntent | S.No. 8**

All users below are **pre-enrolled** on the live Railway deployment with a synthetic legitimate baseline. No setup required — call `/verify` directly.

---

## Live API Base URL
```
https://phantomgrid-production.up.railway.app
```
Swagger UI (interactive testing):
```
https://phantomgrid-production.up.railway.app/docs
```

---

## Pre-Enrolled Test Users

| user_id | Role | Use For |
|---------|------|---------|
| `demo_user` | Primary demo account | API testing via Swagger UI |
| `arjun_4821` | Bank UI account | NexaBank portal (local only) |
| `legit_user` | Secondary demo account | API testing, dashboard filter |

All three are seeded on backend startup with 5 enrollment samples each.

---

## How to Test the Live API (No Setup Needed)

### Option 1 — Swagger UI (Recommended for Judges)
1. Open: `https://phantomgrid-production.up.railway.app/docs`
2. Click `POST /verify` → **Try it out**
3. Paste this body for a **LEGITIMATE session** (should return ALLOW):
```json
{
  "user_id": "demo_user",
  "decoy_tap_count": 0,
  "amount_hesitations": 0,
  "bene_dwell_ms": 605,
  "amount_iki": [112, 96, 103],
  "pin_vector": [119, 91, 108, 84, 100]
}
```
4. Click Execute → Expected response:
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

### Option 2 — Attacker Payload (should return BLOCK)
```json
{
  "user_id": "demo_user",
  "decoy_tap_count": 5,
  "amount_hesitations": 5,
  "bene_dwell_ms": 4000,
  "amount_iki": [600, 650, 700],
  "pin_vector": [400, 350, 500, 300, 450]
}
```
Expected: `"decision": "BLOCK"`, `"composite_score"` near 100.

### Option 3 — curl
```bash
# Legitimate session
curl -X POST https://phantomgrid-production.up.railway.app/verify \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo_user","decoy_tap_count":0,"amount_hesitations":0,"bene_dwell_ms":605,"amount_iki":[112,96,103],"pin_vector":[119,91,108,84,100]}'

# Check session log
curl https://phantomgrid-production.up.railway.app/logs?user_id=demo_user

# Check baseline maturity
curl https://phantomgrid-production.up.railway.app/maturity?user_id=demo_user

# Verify audit chain integrity
curl https://phantomgrid-production.up.railway.app/audit/verify
```

---

## Request Payload Schema

```json
{
  "user_id":            "string  — enrolled user identifier",
  "decoy_tap_count":    "int     — number of decoy element taps (L1)",
  "amount_hesitations": "int     — pauses >300ms on amount field (L1)",
  "bene_dwell_ms":      "int     — milliseconds on beneficiary screen (L2)",
  "amount_iki":         "array   — inter-key intervals on amount field ms (L2)",
  "pin_vector":         "array   — PIN inter-key intervals ms, NOT digits (L3)"
}
```

---

## Local Testing (Backend on localhost)

For the local demo (analyst dashboard + bank UI):

| Account | user_id | How to Use |
|---------|---------|-----------|
| Bank UI / dashboard | `arjun_4821` | Open bank UI with `?enroll=true`, do 5 payment flows |
| Demo scripts | Fresh UUID per run | `python demo_legit.py` and `python demo_attacker.py` auto-generate |
| pytest fixtures | Fresh UUID per test | `conftest.py::fresh_user` generates isolated UUID per test |

---

## Note on PIN Vectors

PhantomGrid **never stores PIN digits**. The `pin_vector` field contains only the timing intervals (milliseconds between consecutive keypresses), not the digits themselves. The values `[118, 92, 107, 85, 99]` represent timing gaps, not the PIN `1-2-3-4-5-6`.

---

*Team ZeroIntent | IIIT Kottayam | CBI Hackathon 2026*
