# Risk Engine Changes — for Person 2 (backend owner)

**Author:** Person 3 · **Date:** 2026-06-20

These are changes to **your backend code** (`services/`). They were made at the
user's explicit request and are documented here so you can review and merge them.
All changes were verified end-to-end against the live backend (8/8 integration
tests pass; live probes confirm legit→ALLOW, attacker→BLOCK).

---

## 1. Decision thresholds — `services/fusion.py`

**Before:** `ALLOW <40 · OTP 40–79 · BLOCK ≥80`
**After:**  `ALLOW <60 · OTP 60–79 · BLOCK ≥80`

```python
if composite < 60:   decision = "ALLOW"   # was < 40
elif composite < 80: decision = "OTP"
else:                decision = "BLOCK"
```
Also: `composite_score` is now `round(...,1)` for clean display.

**Effect:** the "safe" band is wider (0–59). A mid-range session (e.g. composite 50)
is now ALLOW instead of OTP. Matches the requested bands: 0–60 safe, 60–80 OTP, 80–100 block.

---

## 2. Continuous layer scoring (the "always returns 95" fix)

### Problem found (measured, not assumed)
- **L1 & L2 IsolationForest saturate** on the ~5-sample baselines: every anomaly,
  mild or extreme, collapsed to the SAME `decision_function` value
  (L1 ≈ −0.1020, L2 ≈ −0.0099). With the old 4-bucket thresholding this meant:
  - L2 could **never exceed 70** (its anomaly value never passed the −0.1 cutoff).
  - scores never reflected *how* anomalous a session was.
- **L3 (DTW)** produced a perfectly smooth distance but it was thrown into 4 buckets
  (`return 95` for any distance ≥ 100) — hence "95 comes always" for any real mismatch.

### Fix — new file `services/scoring.py`
Two helpers, used by all three layers:

- `continuous_if_risk(training_data, point)` — keeps IsolationForest as the **anomaly
  gate** (inlier vs outlier) but adds a **normalized deviation magnitude** so the score
  ramps smoothly 0–100. Inliers map to 0–45; outliers to 55–100, growing with how far
  the point sits from the enrolled baseline. `_normalized_deviation()` is a per-feature
  z-score magnitude with a std floor (so a near-constant baseline like decoy=0 doesn't
  explode).
- `dtw_to_risk(distance)` — smooth `min(100, distance/180 * 100)`; replaces the 4 buckets.

### Files changed (public function signatures UNCHANGED — `main.py` untouched)
- `services/layer1.py` → `get_layer1_risk()` calls `continuous_if_risk`
- `services/layer2.py` → `get_layer2_risk()` calls `continuous_if_risk`
- `services/layer3.py` → `get_layer3_risk()` calls `dtw_to_risk` (`calculate_distance` unchanged)

### Measured result (live `/verify`, fresh enrollment)
| case | L1 | L2 | L3 | composite | decision |
|------|----|----|----|-----------|----------|
| legit | 4.4 | 1.4 | 0.0 | 1.9 | ALLOW |
| mild attacker | 64.6 | 100 | 42.0 | 72.0 | OTP |
| hard / extreme attacker | 100 | 100 | 100 | 100 | BLOCK |

Scores now gradate smoothly instead of snapping to 10/40/70/95.

---

## 3. Side effect: the demo "pollution" landmine is fixed

**Before:** a legit ALLOW (which your adaptive-learning code appends to the baseline)
dropped a subsequent attacker on the SAME user from BLOCK (85.0) down to OTP (77.5).
**After:** the attacker still scores 100 → BLOCK even after a legit session. The demo is
now order-independent for a strong attacker. (Sustained/gradual poisoning over many
sessions is still a residual risk — see `threat_model/THREAT_MODEL.md` §5.)

---

## 4. Tuning knobs (if you want to adjust)
- Inlier/outlier bands & slopes: the `45.0 / 22.0` and `55.0 / 12.0` constants in
  `continuous_if_risk`.
- DTW sensitivity: the `180.0` divisor in `dtw_to_risk` (smaller = more sensitive).
- Decision cutoffs: `60` / `80` in `fusion.py`.

## 5. Not changed
- `/enroll`, `/verify`, `/logs` request/response shapes — identical.
- Adaptive-learning logic in `main.py` — untouched.
- DTW distance computation — untouched.
