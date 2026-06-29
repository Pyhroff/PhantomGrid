// ═══════════════════════════════════════════════════════════════
// PhantomGrid — JS Behavioral Capture Module
// File: capture.js
// Injected into Nexa_bank_demoUI.html via <script src="capture.js">
//
// LAYER 1 — CognitiveTrap  : decoy tap detection
// LAYER 2 — IntentTrace    : amount field timing + beneficiary dwell
// LAYER 3 — RhythmLock     : PIN inter-key interval capture
// RE-AUTH  — WebAuthn fingerprint (fallback: OTP)
// ═══════════════════════════════════════════════════════════════

(function () {

  // ═══════════════════════════════════════════
  // BACKEND URL — change to Person 2's endpoint
  // ═══════════════════════════════════════════
  var ENROLL_URL = 'http://localhost:8000/enroll';
  var VERIFY_URL = 'http://localhost:8000/verify';
  var API_BASE = 'http://localhost:8000';

  var ENROLL_MODE =
    localStorage.getItem(
      "pg_enroll_mode"
    ) !== "false";

  // ═══════════════════════════════════════════
  // RE-AUTH CONFIG
  // ═══════════════════════════════════════════
  var pendingResult = null;


  // ═══════════════════════════════════════════
  // LAYER 1 — CognitiveTrap
  // ═══════════════════════════════════════════
  var decoyTaps = [];

  window.onDecoyTap = function (name) {
    decoyTaps.push(name);
    console.log('[L1 CognitiveTrap] Decoy tapped:', name);
    console.log('[L1 CognitiveTrap] Total decoy taps:', decoyTaps.length);

    if (decoyTaps.length === 1) {
      window.setRiskLevel('amber', 'Monitoring');
    }
    if (decoyTaps.length >= 3) {
      window.setRiskLevel('red', 'Flagged');
    }
  };


  // ═══════════════════════════════════════════
  // LAYER 2 — IntentTrace: Beneficiary Dwell
  // ═══════════════════════════════════════════
  var beneDwellData = [];

  window.onBeneDwell = function (idx, ms) {
    beneDwellData.push({ idx: idx, dwell_ms: ms });
    console.log('[L2 IntentTrace] Beneficiary', idx, 'selected after', ms, 'ms dwell');

    if (ms > 2000) {
      console.warn('[L2 IntentTrace] ⚠ Long dwell — possible attacker reading carefully');
      window.setRiskLevel('amber', 'Monitoring');
    }
  };


  // ═══════════════════════════════════════════
  // LAYER 2 — IntentTrace: Amount Field Timing
  // ═══════════════════════════════════════════
  var amountIKI = [];
  var lastAmountKeyTime = null;
  var AMT_HESITATION_THRESHOLD = 300;

  window.onAmountKey = function (timestamp) {
    if (lastAmountKeyTime !== null) {
      var gap = timestamp - lastAmountKeyTime;
      amountIKI.push(gap);
      console.log('[L2 IntentTrace] Amount field IKI:', gap, 'ms');
      if (gap > AMT_HESITATION_THRESHOLD) {
        console.warn('[L2 IntentTrace] ⚠ Hesitation in amount field:', gap + 'ms');
      }
    }
    lastAmountKeyTime = timestamp;
  };


  // ═══════════════════════════════════════════
  // LAYER 3 — RhythmLock: PIN Timing
  // ═══════════════════════════════════════════
  var pinIKIVector = [];
  var pinDigits    = [];

  window.onPinKey = function (digit, intervalMs) {
    pinDigits.push(digit);
    if (intervalMs !== null) pinIKIVector.push(intervalMs);

    console.log('[L3 RhythmLock] Digit', pinDigits.length, '| interval:', intervalMs, 'ms');
    console.log('[L3 RhythmLock] IKI vector so far:', pinIKIVector);

    if (pinDigits.length === 6) {
      console.log('=== RhythmLock Complete ===');
      console.log('Full IKI vector:', pinIKIVector);
      console.log('Avg IKI:', Math.round(
        pinIKIVector.reduce(function(a,b){ return a+b; }, 0) / pinIKIVector.length
      ), 'ms');
    }
  };


  // ═══════════════════════════════════════════
  // PAY SUBMIT
  // ═══════════════════════════════════════════
  window.onPaySubmit = function (payload) {

    var signalPackage = {

      user_id: payload.userId,

      decoy_tap_count:
        decoyTaps.length,

      amount_hesitations:
        amountIKI.filter(function(v){
          return v > AMT_HESITATION_THRESHOLD;
        }).length,

      bene_dwell_ms:
        beneDwellData.length > 0
          ? beneDwellData[beneDwellData.length - 1].dwell_ms
          : 0,

      amount_iki:
        amountIKI,

      pin_vector:
        pinIKIVector
    };

    console.log('=== PhantomGrid Signal Package ===');
    console.log(JSON.stringify(signalPackage, null, 2));

    sendToBackend(signalPackage);
  };


  // ═══════════════════════════════════════════
  // SEND TO BACKEND
  // ═══════════════════════════════════════════
function sendToBackend(signalPackage) {

  var endpoint =
    ENROLL_MODE
      ? ENROLL_URL
      : VERIFY_URL;

  console.log(
    '[PhantomGrid] Sending to:',
    endpoint
  );

  fetch(endpoint, {

    method: 'POST',

    headers: {
      'Content-Type':
      'application/json'
    },

    body: JSON.stringify(
      signalPackage
    )

  })

  .then(function(res) {
    return res.json();
  })

  .then(function(result) {

    if (result.error === "User not enrolled") 
    {

      console.warn("[PhantomGrid] Backend has no enrollment data.");

      localStorage.removeItem("pg_enroll_mode");

      ENROLL_MODE = true;

      alert(
        "Enrollment data not found. Starting fresh enrollment."
      );

      return;
    }

    console.log(
      '[PhantomGrid] Response:',
      result
    );

    // ------------------------
    // Enrollment Mode
    // ------------------------

    if (ENROLL_MODE) {

      if (result.message && result.message.includes("/5")) {
        alert(result.message);
      }

      // Switch to verify mode when 5th sample stored ("5/5") OR
      // backend says enrollment already complete
      var done = result.message && (
        result.message.includes("5/5") ||
        result.message.includes("Enrollment") ||
        result.message.includes("complete")
      );

      if (done) {
        ENROLL_MODE = false;
        localStorage.setItem("pg_enroll_mode", "false");
        alert("Enrollment Complete! Switching to live scoring mode.");
      }

      // Re-enable Pay button after enrollment response
      var btn = document.getElementById('pay-btn');
      if (btn) { btn.disabled = false; btn.textContent = 'Pay'; }
      return;
    }

    // ------------------------
    // Verification Mode
    // ------------------------

    // Re-enable Pay button before showing result modal
    var btn = document.getElementById('pay-btn');
    if (btn) { btn.disabled = false; btn.textContent = 'Pay'; }

    handleBackendResult(result);

  })

  .catch(function(err) {
    // Always re-enable the Pay button so user isn't stuck on "Processing..."
    var btn = document.getElementById('pay-btn');
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Pay';
    }
    console.error('[PhantomGrid]', err);

  });
}


  // ═══════════════════════════════════════════
  // RESULT HANDLER
  // Green  → allow directly
  // Amber  → WebAuthn fingerprint, fallback OTP
  // Red    → block immediately
  // ═══════════════════════════════════════════
  function handleBackendResult(result) {

    window.onRiskResult(result);

    console.log(
      '[PhantomGrid] Composite:',
      result.composite_score,
      '| Decision:',
      result.decision
    );

    var decision =
      (result.decision || '')
      .toUpperCase();

    if (decision === 'BLOCK') {

      console.log(
        '[PhantomGrid] 🚨 HIGH RISK — blocking'
      );

      window.setRiskLevel(
        'red',
        'Flagged'
      );

      window.showResult(result);

    }

    else if (decision === 'OTP') {

      console.log(
        '[PhantomGrid] ⚠ OTP REQUIRED'
      );

      window.setRiskLevel(
        'amber',
        'Monitoring'
      );

      pendingResult = result;

      fallbackToOTP();
    }

    else {

      console.log(
        '[PhantomGrid] ✅ LOW RISK — authorized'
      );

      window.setRiskLevel(
        'green',
        'Secure'
      );

      window.showResult(result);

    }
}

  // ═══════════════════════════════════════════
  // OTP FALLBACK
  // ═══════════════════════════════════════════
  function fallbackToOTP() {
    console.log('[PhantomGrid] Showing OTP fallback');
    window.showToast('Additional verification required', 'info');
    window.showOTPOverlay();
  }

  window.onOTPVerified = function(otp) {
    console.log('[PhantomGrid] OTP verified');
    logReAuthEvent('otp_verified', otp.substring(0,2) + '****');
    if (pendingResult) {
      pendingResult.decision = 'allow';
      window.setRiskLevel('green', 'Secure');
      window.showToast('OTP verified ✓', 'success');
      window.showResult(pendingResult);
      pendingResult = null;
    }
  };


  // ═══════════════════════════════════════════
  // LOG RE-AUTH EVENT
  // ═══════════════════════════════════════════
  function logReAuthEvent(eventType, detail) {
    var logPayload = {
      event:     eventType,
      detail:    detail,
      timestamp: Date.now(),
      user_id:   'arjun_4821'
    };
    console.log('[PhantomGrid] Re-auth event:', logPayload);
    fetch(API_BASE + '/reauth-log', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(logPayload)
    }).catch(function() {});
    // silent fail if backend offline — log is not critical path
  }


  // ═══════════════════════════════════════════
  // MOCK RESULT BUILDER
  // ═══════════════════════════════════════════
  function buildMockResult(pkg) {
    var l1 = Math.min(pkg.layer1.decoy_tap_count * 0.25, 1.0);
    var l2 = (Math.min(pkg.layer2.bene_dwell_ms / 5000, 1.0) +
              Math.min(pkg.layer2.amount_hesitations * 0.2, 1.0)) / 2;
    var l3 = Math.min(pkg.layer3.pin_iki_variance / 20000, 1.0);

    var composite = Math.round(((l1 * 0.2) + (l2 * 0.3) + (l3 * 0.5)) * 100) / 100;

    var decision;
    if (composite > AMBER_MAX)       decision = 'block';
    else if (composite >= AMBER_MIN)  decision = 'amber';
    else                              decision = 'allow';

    return {
      decision:        decision,
      composite_score: composite,
      breakdown: {
        layer1: Math.round(l1 * 100) / 100,
        layer2: Math.round(l2 * 100) / 100,
        layer3: Math.round(l3 * 100) / 100
      },
      mock: true
    };
  }


  // ═══════════════════════════════════════════
  // VARIANCE CALCULATOR
  // ═══════════════════════════════════════════
  function calculateVariance(arr) {
    if (arr.length === 0) return 0;
    var mean = arr.reduce(function(a,b){ return a+b; }, 0) / arr.length;
    return Math.round(
      arr.map(function(v){ return Math.pow(v - mean, 2); })
         .reduce(function(a,b){ return a+b; }, 0) / arr.length
    );
  }


  // ═══════════════════════════════════════════
  // SESSION RESET
  // ═══════════════════════════════════════════
  function resetSession() 
  {
    decoyTaps = [];
    beneDwellData = [];
    amountIKI = [];

    lastAmountKeyTime = null;

    pinIKIVector = [];
    pinDigits = [];

    webAuthnAttempts = 0;

    pendingResult = null;

    localStorage.removeItem("pg_enroll_mode");

    console.log('[PhantomGrid] Session reset');
  }
  window.pgResetSession = resetSession;


  // ═══════════════════════════════════════════
  // INIT
  // ═══════════════════════════════════════════
  console.log('=== PhantomGrid Capture Module Loaded ===');
  console.log('Enroll URL:', ENROLL_URL);
  console.log('Verify URL:', VERIFY_URL);
  console.log('Hooks: onDecoyTap, onBeneDwell, onAmountKey, onPinKey, onPaySubmit, onOTPVerified');
  console.log('Re-auth: OTP fallback');

}());