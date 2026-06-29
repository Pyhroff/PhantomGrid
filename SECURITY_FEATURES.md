# PhantomGrid — Advanced Security Features (Person 3)

Three bank-grade features added on top of the core engine. Each has a live demo
command and a one-line judge talking point. **All verified working against the
live backend.**

> **Backend handoff note (for Person 2):** these touch your code — new file
> `services/audit.py`, two columns on `session_logs` (`row_hash`, `prev_hash`,
> auto-migrated on startup), three additions in `main.py` (`/maturity`,
> `/audit/verify`, replay check in `/verify`). Nothing else changed.

---

## 1. Baseline Maturity / Confidence  (cold-start indicator)

**What:** the dashboard shows whether a user's baseline is **mature (5/5)** or still
**building**, with a confidence level. New accounts run at reduced sensitivity until
the baseline matures.

- **Endpoint:** `GET /maturity?user_id=X` → `{samples, required, mature, status, confidence}`
- **Dashboard:** "● Baseline: 5/5 · mature · confidence high" under the gauge.
- **Judge line:** *"We don't pretend a brand-new user is fully protected — the system
  states its own confidence and adapts as it learns. That's honest, deployable ML."*

This **pre-empts the #1 hard question** (cold-start false positives).

---

## 2. Replay-Attack Defense

**What:** a genuine session is never byte-identical twice (rhythm always varies). An
exact-duplicate package is therefore a **replay** — it's detected and forced to **BLOCK**,
and never learned from.

- **Where:** `/verify` computes a SHA-256 signature of the behavioural package; a repeat
  within 5 minutes ⇒ `replay_detected: true`, decision overridden to `BLOCK`.
- **Demo:** `python demo_replay.py`
  ```
  [1] Genuine session runs...      decision = ALLOW   replay_detected = False
  [2] Attacker REPLAYS verbatim... decision = BLOCK   replay_detected = True
  ```
- **Judge line:** *"Even if an attacker sniffs a legit session off the wire and replays
  it byte-for-byte, it fails — behaviour can't be copy-pasted."*

Directly demonstrates the **Spoofing** mitigation from our threat model, live.

---

## 3. Tamper-Evident Audit Trail  (hash-chained logs)

**What:** every `session_logs` row stores `row_hash = SHA256(prev_hash + this row's
fields)`. Editing **any** field of **any** row breaks the chain from that point — so the
log is tamper-evident, which is exactly what RBI audit and the STRIDE **Repudiation**
control require.

- **Endpoint:** `GET /audit/verify` → `{valid, total, verified, broken_at_session}`
- **Dashboard:** header badge "🛡 AUDIT VERIFIED ✓ (N)" — turns red "TAMPERED ✗" if broken.
- **Demo:** `python verify_audit.py --tamper`
  ```
  chain: VALID ✓ (verified 4/4)
  >>> Tampering with one row...
  re-check: TAMPERED ✗ -> broken at session debb3ff8
  restored: VALID ✓
  ```
- **Judge line:** *"Change one number in the database and the integrity check tells you
  exactly which record was altered. Auditors can trust this log."*

---

## Quick demo sequence for these three
```
python demo_legit.py        # ALLOW  — dashboard shows Baseline 5/5 mature
python demo_attacker.py     # BLOCK  — red flash + WHY reasons
python demo_replay.py       # replay caught -> BLOCK
python verify_audit.py --tamper   # tamper detected then restored
```
The dashboard's **🛡 AUDIT VERIFIED ✓** badge and **Baseline maturity** line update live
throughout.
