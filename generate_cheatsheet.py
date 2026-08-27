"""PhantomGrid — 1-page demo day quick reference cheat sheet."""
from fpdf import FPDF

FONT_REG  = 'C:/Windows/Fonts/calibri.ttf'
FONT_BOLD = 'C:/Windows/Fonts/calibrib.ttf'
FONT_ITAL = 'C:/Windows/Fonts/calibrii.ttf'

class CS(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(10, 10, 10)
        self.add_font('C', '',  FONT_REG,  uni=True)
        self.add_font('C', 'B', FONT_BOLD, uni=True)
        self.add_font('C', 'I', FONT_ITAL, uni=True)

p = CS()
p.set_auto_page_break(False)
p.add_page()

W = 190  # usable width

def rule(y=None):
    if y is None: y = p.get_y()
    p.set_draw_color(180,180,180)
    p.set_line_width(0.15)
    p.line(10, y, 200, y)

def hdr(t):
    p.set_font('C','B',7.5)
    p.set_fill_color(30,30,30)
    p.set_text_color(255,255,255)
    p.set_x(10)
    p.cell(W, 4.5, '  ' + t, fill=True, ln=True)
    p.set_text_color(10,10,10)

def row2(label, val, lw=48, extra_height=False):
    p.set_x(10)
    p.set_font('C','B',7.2)
    h = 5.5 if extra_height else 4.2
    p.cell(lw, h, label, ln=False)
    p.set_font('C','',7.2)
    p.multi_cell(W-lw, h, val)

def small(t, indent=10):
    p.set_font('C','',7.0)
    p.set_x(indent)
    p.multi_cell(W - (indent - 10), 3.8, t)

def gap(h=1.5):
    p.ln(h)

# ── TITLE BAR ────────────────────────────────────────────────────────────────
p.set_font('C','B',11)
p.set_text_color(10,10,10)
p.cell(0, 6, 'PhantomGrid  --  Demo Day Quick Reference', align='C', ln=True)
p.set_font('C','I',7)
p.set_text_color(100,100,100)
p.cell(0, 4, 'Team ZeroIntent  |  CBI Hackathon 2026  |  Keep off-screen during Q&A', align='C', ln=True)
p.set_text_color(10,10,10)
gap(1)

rule()
gap(1)

# ── TWO COLUMN LAYOUT ────────────────────────────────────────────────────────
# Left col: 92pt  |  gap: 6pt  |  Right col: 92pt
LC = 10
RC = 108
CW = 92

y_start = p.get_y()

# ════════════════════ LEFT COLUMN ════════════════════
p.set_xy(LC, y_start)

# KEY NUMBERS
p.set_x(LC)
hdr('KEY NUMBERS  (know these cold)')
gap(0.5)

nums = [
    ('Detection rate',        '95.3%   (143/150 attackers caught)'),
    ('False positive rate',   '0.0%    (0/150 legit users flagged)'),
    ('ROC AUC (synthetic)',   '1.000   (perfect separation)'),
    ('ROC AUC (CMU real)',    '0.639   (L3 only, 5 enrollment samples)'),
    ('Precision',             '100.0%  (every flag = real attacker)'),
    ('F1 score',              '0.976'),
    ('False negatives',       '7  (sophisticated mimics, partial rhythm mimic)'),
]
for k,v in nums:
    p.set_x(LC)
    p.set_font('C','B',7.0)
    p.cell(CW*0.45, 4.0, k, ln=False)
    p.set_font('C','',7.0)
    p.multi_cell(CW*0.55, 4.0, v)
gap(1)

# THRESHOLDS & WEIGHTS
p.set_x(LC)
hdr('THRESHOLDS & WEIGHTS')
gap(0.5)
tw = [
    ('Fusion formula',   'L1 x 0.30  +  L2 x 0.40  +  L3 x 0.30'),
    ('ALLOW',            'composite  <  60   (green, transaction proceeds)'),
    ('OTP step-up',      'composite 60-79   (amber, re-authenticate)'),
    ('BLOCK',            'composite >= 80   (red, transaction terminated)'),
    ('Contamination',    '0.10  (IsolationForest tolerance)'),
    ('Baseline window',  '20 sessions (sliding, ALLOW only)'),
    ('DTW -> risk',      'min(100, (distance / 180) x 100)'),
    ('Replay window',    '5 minutes, SHA-256 signature'),
]
for k,v in tw:
    p.set_x(LC)
    p.set_font('C','B',7.0)
    p.cell(CW*0.40, 4.0, k, ln=False)
    p.set_font('C','',7.0)
    p.multi_cell(CW*0.60, 4.0, v)
gap(1)

# LAYERS QUICK REF
p.set_x(LC)
hdr('LAYER SIGNALS')
gap(0.5)
layers = [
    ('L1  CognitiveTrap  (0.30)', 'decoy_tap_count, amount_hesitations  ->  IsolationForest'),
    ('L2  IntentTrace    (0.40)', 'bene_dwell_ms, avg_amount_iki  ->  IsolationForest'),
    ('L3  RhythmLock     (0.30)', 'pin_vector (5 IKI ms)  ->  DTW vs enrolled baseline'),
]
for k,v in layers:
    p.set_x(LC)
    p.set_font('C','B',7.0)
    p.cell(CW, 3.8, k, ln=True)
    p.set_x(LC+4)
    p.set_font('C','',6.8)
    p.multi_cell(CW-4, 3.5, v)
gap(1)

# DEMO COMMANDS
p.set_x(LC)
hdr('DEMO COMMANDS  (have terminals open)')
gap(0.5)
cmds = [
    ('Legitimate user',  'python demo_legit.py'),
    ('Attacker',         'python demo_attacker.py'),
    ('Replay attack',    'python demo_replay.py'),
    ('Backend (local)',  'uvicorn backend.main:app --reload --port 8000'),
    ('Railway URL',      'phantomgrid-production.up.railway.app/docs'),
    ('Demo user',        'demo_user   (seeded synthetic baseline)'),
    ('Dashboard',        'dashboard/index.html?user_id=demo_user'),
]
for k,v in cmds:
    p.set_x(LC)
    p.set_font('C','B',7.0)
    p.cell(CW*0.36, 3.9, k, ln=False)
    p.set_font('C','',7.0)
    p.multi_cell(CW*0.64, 3.9, v)

left_bottom = p.get_y()

# ════════════════════ RIGHT COLUMN ════════════════════
p.set_xy(RC, y_start)

hdr_x = RC

def rhdr(t):
    p.set_font('C','B',7.5)
    p.set_fill_color(30,30,30)
    p.set_text_color(255,255,255)
    p.set_x(RC)
    p.cell(CW, 4.5, '  ' + t, fill=True, ln=True)
    p.set_text_color(10,10,10)

def rrow(label, val, lw=44):
    p.set_x(RC)
    p.set_font('C','B',7.0)
    p.cell(lw, 4.1, label, ln=False)
    p.set_font('C','',7.0)
    p.multi_cell(CW-lw, 4.1, val)

def rsmall(t):
    p.set_font('C','',7.0)
    p.set_x(RC)
    p.multi_cell(CW, 3.8, t)

p.set_xy(RC, y_start)

rhdr('HARDEST JUDGE QUESTIONS')
gap(0.5)

qs = [
    (
        'Q: Why IsolationForest, not neural network?',
        'NNs need 100+ training samples. We enroll with 5. IF works at n=5 with no distributional assumptions -- it\'s the only viable choice at this scale.'
    ),
    (
        'Q: Why not just use MFA?',
        'MFA authenticates once at login. PhantomGrid authenticates continuously. An attacker with stolen credentials + OTP still can\'t fake the victim\'s typing rhythm and navigation habits.'
    ),
    (
        'Q: Your benchmark is synthetic -- is it real?',
        'Synthetic validates engine correctness. We also ran Layer 3 on the CMU real keystroke dataset (51 subjects, 400 reps each): AUC 0.639 on 5 enrollment samples -- honest floor, documented. Path to production: 15-20 enrollment sessions.'
    ),
    (
        'Q: High FPR on CMU -- doesn\'t that mean it fails?',
        'CMU uses a 10-char password with intervals up to 1600ms. Our system is tuned for 5-digit PINs (85-120ms). Dataset mismatch + 5 samples = expected result. Full composite (L1+L2+L3) reduces FPR significantly vs L3 alone.'
    ),
    (
        'Q: Mobile?',
        'Desktop POC only. Mobile needs a native SDK for touch event capture. The ML backend is signal-agnostic -- it takes numerical vectors regardless of source. Mobile is next milestone.'
    ),
    (
        'Q: What about the 7 false negatives?',
        'Sophisticated mimics who partially replicated rhythm (kr=0.08-0.15). Residual risk. Production mitigation: device binding -- even a perfect rhythm mimic must also match the enrolled device fingerprint.'
    ),
    (
        'Q: GDPR / DPDP compliance?',
        'We store derived vectors only, no PII, no keystrokes, no account numbers. Satisfies DPDP Act 2023 data minimisation. RBI data localisation met when deployed India-region.'
    ),
    (
        'Q: How does it scale?',
        'Inference <5ms. Stateless scoring layer scales horizontally. SQLite -> PostgreSQL is one SQLAlchemy line. Redis for baseline lookup in production. No shared mutable state between requests.'
    ),
]

for q, a in qs:
    p.set_x(RC)
    p.set_font('C','B',6.8)
    p.multi_cell(CW, 3.6, q)
    p.set_x(RC+3)
    p.set_font('C','',6.7)
    p.multi_cell(CW-3, 3.5, a)
    gap(1.2)

right_bottom = p.get_y()

# ── BOTTOM STRIP ─────────────────────────────────────────────────────────────
bottom_y = max(left_bottom, right_bottom) + 2
rule(bottom_y)
bottom_y += 1.5

p.set_xy(10, bottom_y)
p.set_font('C','B',7.0)
p.cell(30, 4, 'BEFORE YOU GO ON:', ln=False)
p.set_font('C','',7.0)
p.cell(0, 4, 'Ping Railway 5 min before your slot  |  Open 3 tabs: NexaBank UI + Dashboard + /docs  |  Run demo_legit.py once to confirm backend is live', ln=True)

p.output('C:/Users/LENOVO/OneDrive/Desktop/PhantomGrid/CHEAT_SHEET.pdf')
print(f'Done: {p.page} page -> CHEAT_SHEET.pdf')
