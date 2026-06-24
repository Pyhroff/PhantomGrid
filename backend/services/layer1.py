# Layer 1 — CognitiveTrap
# Training samples: [decoy_tap_count, amount_hesitations]
#
# Continuous scoring (see services/scoring.py). IsolationForest is kept as the
# anomaly gate; the score now ramps smoothly 0–100 with deviation instead of
# snapping to fixed buckets.

from services.scoring import continuous_if_risk


def get_layer1_risk(
    training_data,
    decoy_tap_count,
    amount_hesitations
):
    return continuous_if_risk(
        training_data,
        [decoy_tap_count, amount_hesitations],
    )
