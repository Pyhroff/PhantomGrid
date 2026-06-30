# Layer 2 — IntentTrace
# Training data: [beneficiary_dwell_ms, avg amount inter-key interval ms]
#
# Continuous scoring (see services/scoring.py). This also fixes the old ceiling
# where L2 could never exceed 70 (the IsolationForest anomaly value barely went
# negative, ~-0.01, so the 4-bucket logic capped it).

from services.scoring import continuous_if_risk


def get_layer2_risk(
    training_data,
    bene_dwell_ms,
    amount_iki
):
    avg_amount_iki = sum(amount_iki) / len(amount_iki) if amount_iki else 0.0

    return continuous_if_risk(
        training_data,
        [bene_dwell_ms, avg_amount_iki],
    )
