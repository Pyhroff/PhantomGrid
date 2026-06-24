def fusion_score(layer1, layer2, layer3):

    composite = (

        0.3 * layer1 +

        0.4 * layer2 +

        0.3 * layer3
    )

    # Decision bands (updated):
    #   0–59   -> ALLOW  (safe)
    #   60–79  -> OTP    (step-up re-auth)
    #   80–100 -> BLOCK
    if composite < 60:

        decision = "ALLOW"

    elif composite < 80:

        decision = "OTP"

    else:

        decision = "BLOCK"

    return {
        "composite_score": round(composite, 1),
        "decision": decision
    }
