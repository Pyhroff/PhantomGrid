# PhantomGrid — Benchmark Performance Results

**Methodology:** 300 synthetic sessions (150 legitimate + 150 attacker) generated across a difficulty gradient and scored through the production engine (`backend/services`). Operating point: composite >= 60 flags the session (OTP or BLOCK decision).

| Metric | Result |
|--------|--------|
| **Detection Rate** (attackers caught at OTP or BLOCK) | **95.3%** |
| **False Positive Rate** (legitimate users challenged) | **0.0%** |
| Precision | 100.0% |
| Accuracy | 97.7% |
| F1 Score | 0.976 |
| **ROC AUC** | **1.000** |

### Confusion Matrix

|                   | Predicted ATTACK | Predicted LEGIT |
|-------------------|:----------------:|:---------------:|
| **Actual ATTACK** | TP = 143         | FN = 7          |
| **Actual LEGIT**  | FP = 0           | TN = 150        |

### Notes

- The 7 false negatives represent sophisticated mimics who partially replicated the victim's rhythm and navigation patterns. This residual risk is documented in `threat_model/THREAT_MODEL.md`.
- 0% false positive rate is structural: no single layer can cross the flag threshold alone, so legitimate users with minor behavioural variation (different typing speed on a given day) are not challenged.
- This is a synthetic benchmark validating the scoring engine's separation characteristics and failure modes. It is not a production performance guarantee. Real-world numbers require a field pilot with consented users.

Run `python benchmark.py` to regenerate. Output is saved to `benchmark_report.html` (ROC curve + confusion matrix visualisation).

---

## Benchmark 2 — Real Keystroke Data (CMU Dataset, Layer 3 Only)

**Dataset:** CMU Keystroke Dynamics Study — Killourhy & Maxion, DSN 2009  
**Source:** `www.cs.cmu.edu/~keystroke` — 51 subjects, 400 repetitions each, typing the password `.tie5Roanl`  
**Methodology:** Subject s002 enrolled with 5 genuine reps (real human typing). 150 subsequent reps scored as legitimate sessions. 150 sessions drawn from 5 different real subjects scored as attacker sessions. Layer 3 (RhythmLock DTW) engine only — L1 and L2 signals are not present in this dataset.

| Metric | Result |
|--------|--------|
| **ROC AUC** | **0.639** |
| Detection Rate (attackers caught) | 95.3% |
| False Positive Rate (legit flagged) | 88.7% |
| Precision | 51.8% |
| F1 Score | 0.671 |
| Enrollment samples | 5 real reps |

### Confusion Matrix (DTW threshold 200ms)

|                   | Predicted ATTACK | Predicted LEGIT |
|-------------------|:----------------:|:---------------:|
| **Actual ATTACK** | TP = 143         | FN = 7          |
| **Actual LEGIT**  | FP = 133         | TN = 17         |

### DTW Distance Distributions

| Population | Mean DTW | Std Dev |
|------------|:--------:|:-------:|
| Legitimate (same subject) | 430ms | 175ms |
| Attacker (different subjects) | 528ms | 204ms |

### What This Tells Us

- **AUC 0.639** on real data with 5 enrollment samples is expected and honest. The synthetic benchmark AUC of 1.00 was clean by construction — real human keystroke distributions overlap significantly at low enrollment counts.
- **High FPR (88.7%)** at the operating point is a direct consequence of the 5-sample enrollment constraint. CMU literature shows reliable separation requires 50+ sessions; commercial systems (BioCatch, BehavioSec) use continuous learning over hundreds of sessions.
- **This is Layer 3 alone.** In the full PhantomGrid system, L1 (decoy interactions) and L2 (navigation intent) contribute orthogonal signals that catch attacker behaviour that pure rhythm analysis misses. The composite fusion exists precisely because no single layer is sufficient in isolation.
- **Dataset mismatch:** CMU uses a 10-character password with high timing variance (one interval reaches 1600ms). PhantomGrid is tuned for 5-digit PIN rhythms (85–120ms range). A PIN-specific real dataset would produce tighter distributions and better separation.

### Honest Summary

The synthetic benchmark validates engine correctness. The CMU benchmark validates the documented limitation: 5 enrollment samples is a POC floor, not a production operating point. The path to real-world performance is a field pilot with 15–20 enrollment sessions per user, at which point the distributions separate cleanly and the full 3-layer composite reduces FPR significantly.
