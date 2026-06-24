# Layer 3 — RhythmLock (DTW)
#
# calculate_distance() is unchanged. get_layer3_risk() now maps the DTW distance
# to a SMOOTH 0–100 score instead of the old 4 buckets (which returned a flat 95
# for any distance >= 100). See services/scoring.py.

from dtaidistance import dtw

from services.scoring import dtw_to_risk


def calculate_distance(baseline_vector, current_vector):
    """Returns DTW distance between stored baseline vector and current PIN vector."""
    return dtw.distance(baseline_vector, current_vector)


def get_layer3_risk(distance):
    """Converts DTW distance into a continuous 0–100 risk score."""
    return dtw_to_risk(distance)
