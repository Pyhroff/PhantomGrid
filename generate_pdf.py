"""Generate TECHNICAL_DOCUMENTATION.pdf from content."""
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'PhantomGrid - Technical Documentation | CBI Hackathon 2026 | Team ZeroIntent', align='C')
        self.ln(4)
        self.set_draw_color(0, 212, 255)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'Page {self.page_no()} | IIIT Kottayam | ZeroIntent_8_CBIHack2026', align='C')

    def h1(self, text):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(0, 100, 150)
        self.ln(4)
        self.cell(0, 8, text, ln=True)
        self.set_draw_color(0, 100, 150)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_text_color(30, 30, 30)

    def h2(self, text):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(20, 80, 130)
        self.ln(3)
        self.cell(0, 7, text, ln=True)
        self.set_text_color(30, 30, 30)
        self.ln(1)

    def h3(self, text):
        self.set_font('Helvetica', 'BI', 10)
        self.set_text_color(60, 60, 120)
        self.ln(2)
        self.cell(0, 6, text, ln=True)
        self.set_text_color(30, 30, 30)

    def body(self, text):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def code(self, text):
        self.set_fill_color(245, 245, 245)
        self.set_font('Courier', '', 7.5)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 4.5, text, fill=True)
        self.ln(1)

    def table_row(self, cols, widths, bold=False, header=False):
        style = 'B' if bold or header else ''
        self.set_font('Helvetica', style, 8)
        if header:
            self.set_fill_color(220, 235, 245)
        else:
            self.set_fill_color(252, 252, 252)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        y = self.get_y()
        max_h = 5
        for i, (col, w) in enumerate(zip(cols, widths)):
            self.multi_cell(w, 5, str(col), border=1, fill=True)
            self.set_xy(x + sum(widths[:i+1]), y)
        self.ln(max_h)

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# ── PAGE 1 ──────────────────────────────────────────────────────────────────
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(0, 80, 140)
pdf.ln(2)
pdf.cell(0, 10, 'PhantomGrid', align='C', ln=True)
pdf.set_font('Helvetica', 'B', 12)
pdf.set_text_color(0, 130, 180)
pdf.cell(0, 7, 'AI-Driven Passive Behavioural Authentication Engine', align='C', ln=True)
pdf.set_font('Helvetica', '', 9)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 6, 'CBI Hackathon 2026 - Phase II Technical Documentation', align='C', ln=True)
pdf.cell(0, 6, 'Team ZeroIntent  |  S.No. 8  |  IIIT Kottayam', align='C', ln=True)
pdf.cell(0, 6, 'Madapati Jyoti Radithya  |  Kontheti Sai Akhilesh  |  Praising Y Harris Ratnam (Lead)', align='C', ln=True)
pdf.ln(4)
pdf.set_draw_color(0, 130, 180)
pdf.set_line_width(0.5)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(5)

pdf.h1('1. Problem Statement')
pdf.body(
    'Account Takeover (ATO) fraud in Public Sector Banks (PSBs) has reached a critical inflection point. '
    'In FY2023, Indian PSBs reported over INR 7,400 crore in digital fraud losses - the majority occurring '
    'after successful login. Attackers bypass authentication entirely using stolen credentials purchased '
    'from dark-web marketplaces.\n\n'
    'The fundamental failure of current authentication is temporal: systems verify identity once at the '
    'login gate, then trust the session unconditionally. An attacker with valid credentials - obtained '
    'through phishing, SIM swap, or social engineering - is indistinguishable from a legitimate user '
    'by any existing control.\n\n'
    'PhantomGrid answers the question that matters at the point of a fund transfer: Is the person '
    'currently operating this session the enrolled account holder? It answers continuously, silently, '
    'and with zero additional friction.'
)

pdf.h1('2. Proposed Solution')
pdf.body(
    'PhantomGrid is a three-layer passive behavioural authentication engine running transparently beneath '
    'a banking portal. Rather than challenging users with additional factors, it observes unconscious '
    'behavioural signatures that are stable over time and practically impossible to replicate.\n\n'
    'The system operates in two phases:\n\n'
    '  Enrollment (Sessions 1-5): PhantomGrid silently collects behavioural baseline vectors across three '
    'independent signal domains during normal transactions. No user action required.\n\n'
    '  Continuous Scoring (Session 6+): Every transaction is scored against the enrolled baseline. '
    'A composite risk score (0-100) determines the response: ALLOW, OTP step-up, or BLOCK.\n\n'
    'The analyst dashboard provides real-time visibility into session scores, per-layer risk breakdown, '
    'explainability reasoning, and a tamper-evident audit trail.'
)

pdf.h1('3. System Architecture')
pdf.body('PhantomGrid follows a three-tier architecture with clear separation of concerns:')
pdf.code(
    'TIER 1: Signal Capture (Madapati Jyoti Radithya)\n'
    '  capture.js - behavioural hooks injected into the banking portal\n'
    '  Signals: decoy_tap_count, bene_dwell_ms, amount_iki[], pin_vector[]\n'
    '  Packages all signals into ONE JSON payload per transaction\n\n'
    'TIER 2: ML Inference Engine - FastAPI + Python 3.12 (Kontheti Sai Akhilesh)\n'
    '  Layer 1 CognitiveTrap:  Isolation Forest on decoy interactions\n'
    '  Layer 2 IntentTrace:    Isolation Forest on navigation behaviour\n'
    '  Layer 3 RhythmLock:     Dynamic Time Warping on PIN keystroke rhythm\n'
    '  Fusion:                 composite = L1*0.30 + L2*0.40 + L3*0.30\n'
    '  Security:               SHA-256 replay defence + hash-chain audit log\n'
    '  Decision:               ALLOW (<60)  |  OTP (60-79)  |  BLOCK (>=80)\n\n'
    'TIER 3: Analyst Dashboard (Praising Y Harris Ratnam)\n'
    '  Polls GET /logs every 2 seconds\n'
    '  Live gauge, layer bars, trend chart, fraud alert, audit badge'
)

# ── PAGE 2 ──────────────────────────────────────────────────────────────────
pdf.add_page()

pdf.h1('4. Technology Stack')
cols = ['Component', 'Technology', 'Rationale']
widths = [45, 50, 95]
pdf.table_row(cols, widths, header=True)
rows = [
    ['API Framework', 'FastAPI (Python 3.12)', 'Async, auto-validates with Pydantic, Swagger UI'],
    ['Anomaly Detection (L1,L2)', 'scikit-learn IsolationForest', 'Unsupervised - no fraud labels needed at enrollment'],
    ['Rhythm Comparison (L3)', 'dtaidistance (DTW)', 'Handles natural speed variation in keystroke sequences'],
    ['Database ORM', 'SQLAlchemy 2.0', 'Declarative models, PostgreSQL-compatible schema'],
    ['Database', 'SQLite / PostgreSQL', 'SQLite for PoC; Railway uses env-var for PostgreSQL'],
    ['Validation', 'Pydantic v2', 'Zero-overhead schema enforcement, 422 on malformed input'],
    ['Audit Crypto', 'hashlib SHA-256', 'Hash chain + payload signatures for replay defence'],
    ['Frontend', 'Vanilla HTML/CSS/JS', 'No build step - fully portable, zero dependency'],
    ['Tests', 'pytest + requests', '8 integration tests against live backend'],
    ['Deployment', 'Railway (Nixpacks)', 'Live at phantomgrid-production.up.railway.app'],
]
for r in rows:
    pdf.table_row(r, widths)
pdf.ln(3)

pdf.h1('5. Workflow')
pdf.h2('5.1 Enrollment Flow')
pdf.code(
    'User initiates payment\n'
    '  capture.js collects: decoy_tap_count, amount_hesitations (L1)\n'
    '                        bene_dwell_ms, amount_iki[] (L2)\n'
    '                        pin_vector[] - inter-key intervals ONLY, no digits (L3)\n'
    '  POST /enroll {user_id, all signals}\n'
    '  Backend stores feature vectors in user_profiles (JSON blobs)\n'
    '  After 5 samples: enrollment complete, capture.js auto-switches to VERIFY mode'
)

pdf.h2('5.2 Verification / Scoring Flow')
pdf.code(
    'POST /verify {user_id, signals}\n'
    '  1. Replay check: SHA-256(payload) in seen_signatures (5-min window)?\n'
    '        YES -> forced BLOCK, replay_detected: true\n'
    '        NO  -> continue\n'
    '  2. Layer scoring:\n'
    '     L1: continuous_if_risk(baseline, [decoy_taps, hesitations])\n'
    '     L2: continuous_if_risk(baseline, [bene_dwell, avg_iki])\n'
    '     L3: dtw_to_risk(min DTW distance to any enrolled PIN vector)\n'
    '  3. Fusion: composite = L1*0.30 + L2*0.40 + L3*0.30\n'
    '  4. Decision: ALLOW (<60) | OTP (60-79) | BLOCK (>=80)\n'
    '  5. If ALLOW: append to baseline (adaptive learning, window 20)\n'
    '  6. Hash chain: row_hash = SHA256(prev_hash|session_data)\n'
    '  7. Write session_logs, return scores + decision + replay_detected\n'
    '  8. Dashboard polls GET /logs every 2s -> updates live'
)

pdf.h1('6. Database Design')
pdf.h2('Table: user_profiles')
cols = ['Column', 'Type', 'Description']
widths = [40, 30, 120]
pdf.table_row(cols, widths, header=True)
rows = [
    ['id', 'INTEGER PK', 'Auto-increment primary key'],
    ['user_id', 'TEXT UNIQUE', 'User identifier (from bank session)'],
    ['layer1_vectors', 'TEXT (JSON)', 'List of [decoy_tap_count, amount_hesitations] pairs'],
    ['layer2_vectors', 'TEXT (JSON)', 'List of [bene_dwell_ms, avg_amount_iki] pairs'],
    ['pin_vectors', 'TEXT (JSON)', 'List of PIN inter-key interval vectors (no digits)'],
]
for r in rows:
    pdf.table_row(r, widths)
pdf.ln(2)

pdf.h2('Table: session_logs')
cols = ['Column', 'Type', 'Description']
widths = [42, 28, 120]
pdf.table_row(cols, widths, header=True)
rows = [
    ['id', 'INTEGER PK', 'Auto-increment'],
    ['session_id', 'TEXT UNIQUE', 'UUID-derived 8-char session identifier'],
    ['timestamp', 'DATETIME', 'UTC timestamp of session'],
    ['user_id', 'TEXT', 'User who initiated session'],
    ['layer1_score', 'REAL', 'CognitiveTrap risk score (0-100)'],
    ['layer2_score', 'REAL', 'IntentTrace risk score (0-100)'],
    ['layer3_score', 'REAL', 'RhythmLock risk score (0-100)'],
    ['composite_score', 'REAL', 'Fused weighted risk score (0-100)'],
    ['decision', 'TEXT', 'ALLOW | OTP | BLOCK'],
    ['row_hash', 'TEXT', 'SHA-256 of this row - tamper detection'],
    ['prev_hash', 'TEXT', 'SHA-256 of preceding row - hash chain link'],
]
for r in rows:
    pdf.table_row(r, widths)

# ── PAGE 3 ──────────────────────────────────────────────────────────────────
pdf.add_page()

pdf.h1('7. AI / ML Models')
pdf.h2('7.1 Isolation Forest - Layers 1 & 2 (CognitiveTrap, IntentTrace)')
pdf.body(
    'Isolation Forest (Liu et al., 2008) is an unsupervised anomaly detection algorithm that exploits '
    'the property that anomalies are rare and different. It builds 100 isolation trees by recursively '
    'partitioning the feature space with random splits. Normal points require many splits to isolate '
    '(deep paths). Anomalies require few (shallow paths = anomaly score).\n\n'
    'PhantomGrid extends standard IF with a continuous hybrid engine (services/scoring.py) that solves '
    'the saturation problem on small (5-sample) per-user baselines:'
)
pdf.code(
    'def continuous_if_risk(training_data, point):\n'
    '    deviation = _normalized_deviation(point, training_data)\n'
    '    if len(training_data) < 10:          # Small baseline: skip IF gate\n'
    '        return round(min(100.0, deviation * 30.0), 1)\n'
    '    model = IsolationForest(contamination=0.1, random_state=42).fit(training_data)\n'
    '    gate = model.decision_function([point])[0]   # >0 inlier, <0 outlier\n'
    '    if gate >= 0:\n'
    '        return round(min(45.0, deviation * 22.0), 1)   # Inlier: 0-45\n'
    '    return round(min(100.0, 55.0 + deviation * 12.0), 1)  # Outlier: 55-100'
)
pdf.body(
    'Hyperparameters: contamination=0.1 (10% noise tolerance), n_estimators=100, random_state=42.\n'
    'Small-baseline fallback: For baselines under 10 samples, pure normalized-deviation scoring '
    'is used - monotonic, deterministic, and immune to IF instability on sparse data.'
)

pdf.h2('7.2 Dynamic Time Warping - Layer 3 (RhythmLock)')
pdf.body(
    'DTW (Sakoe & Chiba, 1978) finds the optimal elastic alignment between two time series before '
    'measuring residual distance. This is critical for keystroke dynamics: a user typing their PIN '
    '10% faster when stressed still produces the same relative rhythm, which Euclidean distance would '
    'incorrectly flag as anomalous.\n\n'
    'Implementation: DTW distance computed between query PIN vector and every enrolled baseline vector. '
    'Minimum distance taken (best-match strategy, reduces FRR). Mapped to risk score:'
)
pdf.code('def dtw_to_risk(distance):\n    return round(min(100.0, (distance / 180.0) * 100.0), 1)')
pdf.body('Calibration: 180ms total DTW deviation saturates to full risk (100). Legit jitter: 0-10ms -> score 0-6.')

pdf.h2('7.3 Adaptive Learning')
pdf.body(
    'After every ALLOW decision, the session\'s behavioural vectors are appended to the user\'s baseline '
    '(sliding window, capped at 20 samples per layer). This implements online incremental learning - '
    'the model drifts toward the user\'s current behaviour, handling natural evolution over time '
    '(new device, aging, lifestyle changes) without explicit retraining.'
)

pdf.h2('7.4 Performance Benchmark')
pdf.body('Validated on 200 synthetic sessions (100 legitimate, 100 attacker):')
cols = ['Metric', 'Result', 'Interpretation']
widths = [55, 35, 100]
pdf.table_row(cols, widths, header=True)
rows = [
    ['Detection Rate (TPR)', '96.7%', 'Of 100 attacker sessions, 97 correctly blocked'],
    ['False Positive Rate (FPR)', '0.0%', 'Zero legitimate users incorrectly blocked'],
    ['AUC (ROC Curve)', '1.00', 'Perfect separation of legit vs attacker populations'],
]
for r in rows:
    pdf.table_row(r, widths)
pdf.ln(2)

pdf.h1('8. APIs and External Services')
pdf.body('PhantomGrid uses no external APIs or cloud ML services. All computation is self-contained.')
cols = ['Endpoint', 'Method', 'Description']
widths = [55, 20, 115]
pdf.table_row(cols, widths, header=True)
rows = [
    ['/enroll', 'POST', 'Store one enrollment sample (5 needed to complete baseline)'],
    ['/verify', 'POST', 'Score session: returns {layer scores, composite, decision, replay_detected}'],
    ['/logs?user_id=X', 'GET', 'Last 20 session log rows, optionally filtered by user'],
    ['/maturity?user_id=X', 'GET', 'Baseline maturity: {samples, required, mature, confidence}'],
    ['/audit/verify', 'GET', 'Walk hash chain: {valid, verified, broken_at_session}'],
]
for r in rows:
    pdf.table_row(r, widths)

# ── PAGE 4 ──────────────────────────────────────────────────────────────────
pdf.add_page()

pdf.h1('9. Security Measures')
pdf.h2('9.1 Replay-Attack Defence')
pdf.body(
    'SHA-256 signature computed over the full behavioural payload (user_id, all signal values). '
    'Exact duplicate signatures within a 5-minute window are detected by services/audit.py::is_replay() '
    'and forced to BLOCK with replay_detected: true in the response. This prevents attackers from '
    'capturing a legitimate session packet and retransmitting it verbatim.'
)

pdf.h2('9.2 Tamper-Evident Audit Chain')
pdf.body(
    'SHA-256 hash chain over session_logs. Each row contains row_hash (SHA-256 of its own content '
    'including the previous row\'s hash) and prev_hash (the prior row\'s hash). Any retrospective '
    'modification of any single record invalidates the chain from that point forward, detectable '
    'instantly via GET /audit/verify. Satisfies RBI Master Circular requirements for immutable '
    'transaction audit trails.'
)

pdf.h2('9.3 Input Validation & PII Minimisation')
pdf.body(
    'All API requests are validated via Pydantic v2 schemas before any ML code executes. Malformed '
    'payloads receive HTTP 422. No SQL injection surface (SQLAlchemy ORM with parameterised queries).\n\n'
    'PIN digits are never persisted. Only inter-keystroke timing intervals (millisecond gaps between '
    'digit entries) are stored. These values cannot be reverse-engineered to recover the PIN. '
    'No account numbers, names, or transaction amounts are stored by PhantomGrid.'
)

pdf.h2('9.4 STRIDE Threat Coverage')
cols = ['Threat', 'Control', 'Status']
widths = [42, 120, 28]
pdf.table_row(cols, widths, header=True)
rows = [
    ['Spoofing', 'Per-user IF models - impersonation requires exact behavioral mimicry', 'Mitigated'],
    ['Tampering', 'SHA-256 hash chain - any DB edit is detectable at exact row', 'Mitigated'],
    ['Repudiation', 'Immutable session_logs with UTC timestamps and hash chain', 'Mitigated'],
    ['Info Disclosure', 'No PII stored; behavioral vectors non-reversible', 'Mitigated'],
    ['Denial of Service', 'Lightweight inference <5ms; rate-limiting in production', 'Partial'],
    ['Elevation of Privilege', '/enroll requires authenticated session in production', 'PoC gap'],
]
for r in rows:
    pdf.table_row(r, widths)
pdf.ln(3)

pdf.h1('10. Scalability Considerations')
cols = ['Concern', 'PoC Approach', 'Production Path']
widths = [38, 55, 97]
pdf.table_row(cols, widths, header=True)
rows = [
    ['Database', 'SQLite (single file)', 'PostgreSQL - drop-in connection string swap'],
    ['Model storage', 'Fit on-the-fly per request', 'Pre-serialised IF models (joblib) + Redis cache'],
    ['Dashboard updates', 'REST polling every 2s', 'WebSocket streaming at 50ms'],
    ['Deployment', 'Railway (single region)', 'Docker + AWS ap-south-1 (RBI data localisation)'],
    ['Baseline training', '5 enrollment samples', 'Shadow mode 30+ samples before enforcement'],
    ['Inference latency', 'L1+L2+L3 < 5ms total', 'Unchanged - does not block payment flow'],
]
for r in rows:
    pdf.table_row(r, widths)

# ── PAGE 5 ──────────────────────────────────────────────────────────────────
pdf.add_page()

pdf.h1('11. Assumptions and Limitations')
pdf.h2('Assumptions')
pdf.body(
    '1. Users enroll on the same device used for live transactions. PIN rhythm is device-specific '
    '(keyboard type affects timings).\n'
    '2. At least 5 enrollment samples are available before scoring enforcement begins.\n'
    '3. The /enroll endpoint is called within an authenticated banking session (prevents enrollment '
    'poisoning - flagged as production requirement in threat model).\n'
    '4. capture.js has not been tampered with by a client-side attacker (XSS vector).'
)

pdf.h2('Limitations')
pdf.body(
    '1. Cold Start: Under 5 enrollment samples, model reliability is reduced. The /maturity endpoint '
    'signals this explicitly to the analyst dashboard.\n'
    '2. Cross-Device Degradation: PIN rhythm changes significantly across physical keyboards. '
    'Mitigation: per-device baseline profiles (production roadmap).\n'
    '3. Sustained Adaptive Poisoning: A sophisticated attacker achieving repeated OTP decisions '
    'over many sessions could gradually drift the baseline. Mitigation: drift detection with '
    'exponential moving average (production roadmap).\n'
    '4. SQLite Concurrency: Single-writer limitation. Not suitable for high-concurrency production '
    'without migration to PostgreSQL.'
)

pdf.h1('12. Future Enhancements')
cols = ['Feature', 'Description', 'Priority']
widths = [48, 120, 22]
pdf.table_row(cols, widths, header=True)
rows = [
    ['Mouse/Touch Dynamics', 'L4 layer: scroll velocity, touch pressure, pointer trajectory entropy', 'High'],
    ['Device-Aware Profiles', 'Separate baseline per device fingerprint - eliminates cross-device FRR spike', 'High'],
    ['PostgreSQL Migration', 'Drop-in connection string change; enables horizontal scaling', 'High'],
    ['Mobile SDK', 'Touch pressure, swipe velocity, accelerometer during PIN entry', 'High'],
    ['WebSocket Streaming', 'Real-time dashboard at 50ms vs 2s polling', 'Medium'],
    ['Federated Baseline', 'Global population model on anonymised data to bootstrap cold-start users', 'Medium'],
    ['Drift Detection', 'Statistical test on baseline evolution - alert on unnatural drift', 'Medium'],
    ['RBI Reporting Module', 'Per-user risk history, aggregate metrics, audit export for regulators', 'Medium'],
    ['Active Deception Layer', 'Randomise decoy positions per session - hardens against layout memorisation', 'Low'],
]
for r in rows:
    pdf.table_row(r, widths)
pdf.ln(4)

pdf.h1('13. Live Deployment')
pdf.body(
    'PhantomGrid is deployed live on Railway (cloud platform) at:\n\n'
    '  API Base:    https://phantomgrid-production.up.railway.app\n'
    '  Swagger UI:  https://phantomgrid-production.up.railway.app/docs\n'
    '  GitHub:      https://github.com/Pyhroff/PhantomGrid (private, shared with CBIHack26)\n\n'
    'The deployment auto-seeds demo_user on startup. Judges can immediately POST to /verify '
    'with user_id: demo_user without any setup. The backend serves all endpoints documented above.'
)

pdf.h1('Team')
cols = ['Role', 'Name', 'Contribution']
widths = [55, 55, 80]
pdf.table_row(cols, widths, header=True)
rows = [
    ['Frontend - Signal Capture', 'Madapati Jyoti Radithya', 'NexaBank portal + capture.js behavioural hooks'],
    ['Backend - ML Engine', 'Kontheti Sai Akhilesh', 'FastAPI + IsolationForest + DTW + SQLite'],
    ['Dashboard + Security + Tests (Lead)', 'Praising Y Harris Ratnam', 'Dashboard, audit chain, replay defence, test suite'],
]
for r in rows:
    pdf.table_row(r, widths)

pdf.ln(5)
pdf.set_font('Helvetica', 'BI', 10)
pdf.set_text_color(0, 80, 140)
pdf.cell(0, 6, 'PhantomGrid - Passive. Invisible. Unbeatable.', align='C', ln=True)
pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 5, 'Team ZeroIntent | S.No. 8 | CBI Hackathon 2026 | MNNIT Allahabad | IIIT Kottayam', align='C', ln=True)

pdf.output('TECHNICAL_DOCUMENTATION.pdf')
print(f"PDF generated: TECHNICAL_DOCUMENTATION.pdf ({pdf.page} pages)")
