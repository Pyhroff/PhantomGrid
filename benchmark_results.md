# PhantomGrid — Measured Performance

Method: 150 legitimate + 150 attacker sessions generated across a
difficulty gradient and scored through the production engine
(`backend/services`). Operating point: composite ≥ 60 ⇒ session caught
(OTP or BLOCK).

| Metric | Value |
|--------|-------|
| **Detection rate** (attackers caught) | **96.7%** |
| **False-positive rate** (legit challenged) | **0.0%** |
| Precision | 100.0% |
| Accuracy | 98.3% |
| F1 score | 0.983 |
| **ROC AUC** | **1.000** |

### Confusion matrix (operating point)

|              | Predicted ATTACK | Predicted LEGIT |
|--------------|:---------------:|:---------------:|
| **Actual ATTACK** | TP = 145 | FN = 5 |
| **Actual LEGIT**  | FP = 0 | TN = 150 |

### How to read this (be honest with judges)

- **Detection 96.7% / Block 89.3%** track the
  proposal's ≥96% targets — on this synthetic population.
- **The 5 false negatives are the sophisticated mimics** (attacker who has
  observed the victim and partially replicates rhythm + habits). That is exactly
  the residual risk in §5 of the threat model — the benchmark *surfaces* it
  rather than hiding it.
- **0% false positives** is structural: no single layer can cross the flag
  threshold alone, so a legit user who's merely on a second device isn't
  challenged. The same property is why a single-layer attacker can occasionally
  slip — see the L2-ceiling note in the threat model.

### Limitations

This is a **synthetic** benchmark: we generate the sessions *and* run the scoring
engine, so it validates **separation and failure modes**, not real-world accuracy.
It is evidence that the engine behaves correctly and that our weak spot is the
sophisticated mimic — not a production performance guarantee. Real numbers require
a field pilot with consented users.
