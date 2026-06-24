"""
Shared continuous-scoring helpers for Layers 1–3.

WHY THIS EXISTS
---------------
The original layer scorers bucketed into 4 fixed values (10/40/70/95). Two
problems showed up when measured against real inputs:

  * IsolationForest.decision_function SATURATES on the tiny (~5 sample) per-user
    baselines: every anomaly — mild or extreme — collapsed to the same value
    (L1 ≈ -0.10, L2 ≈ -0.01). So L2 could never exceed 70, and the score never
    reflected *how* anomalous a session was.
  * DTW (Layer 3) already produces a smooth distance, but it was thrown away
    into 4 buckets ("return 95" for anything past 100).

These helpers keep IsolationForest as the anomaly GATE (inlier vs outlier) but
add a continuous deviation MAGNITUDE, so scores ramp smoothly 0–100. DTW is
mapped continuously instead of bucketed.
"""

import math
from statistics import mean, pstdev

from sklearn.ensemble import IsolationForest


def _normalized_deviation(point, training_data):
    """Per-feature z-style deviation magnitude from the baseline.

    Robust to near-zero spread: each feature's std is floored so a baseline with
    almost no variance (e.g. decoy_tap_count always 0) doesn't explode to huge
    ratios. Returns a non-negative scalar (0 = exactly at baseline mean)."""
    cols = list(zip(*training_data))
    total = 0.0
    for i, x in enumerate(point):
        mu = mean(cols[i])
        sd = pstdev(cols[i])
        floor = max(1.0, abs(mu) * 0.15)
        sd = max(sd, floor)
        total += ((x - mu) / sd) ** 2
    return math.sqrt(total / len(point))


def continuous_if_risk(training_data, point):
    """IsolationForest anomaly gate + normalized-deviation magnitude -> 0–100.

    Inliers ramp gently inside 0–45; outliers start at 55 and grow with how far
    the point sits from the enrolled baseline. Monotonic and smooth."""
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(training_data)

    gate = model.decision_function([point])[0]   # >0 normal, <0 anomaly
    deviation = _normalized_deviation(point, training_data)

    if gate >= 0:
        risk = min(45.0, deviation * 22.0)
    else:
        risk = min(100.0, 55.0 + deviation * 12.0)
    return round(risk, 1)


def dtw_to_risk(distance):
    """Smooth DTW distance -> 0–100 risk (replaces the old 4-bucket mapping).

    distance 0 -> 0 risk; distance >= ~180 -> 100. Genuine PIN-rhythm matches
    sit near 0; a different person's rhythm climbs continuously to 100."""
    return round(min(100.0, (distance / 180.0) * 100.0), 1)
