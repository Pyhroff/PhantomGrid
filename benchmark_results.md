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
