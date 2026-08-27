# PhantomGrid — Demo Video Script
# CBI Hackathon 2026 | Team ZeroIntent | S.No. 8
# Target: 6–7 minutes | Single continuous take | No editing

---

## BEFORE YOU HIT RECORD — SETUP CHECKLIST

- [ ] Backend running: `cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000`
- [ ] Dashboard server: `cd dashboard && python -m http.server 5599`
- [ ] Dashboard open in browser tab: `http://localhost:5599`
- [ ] Bank UI open in second tab: `Nexa_bank_demoUI.html`
- [ ] Terminal 3 open at project root, ready for commands
- [ ] OBS recording: 1080p, system audio ON (for the BLOCK beep)
- [ ] Phone on silent, notifications off
- [ ] Read the script out loud once before recording

---

## THE SCRIPT

---

### [0:00 – 0:30] INTRODUCTION

**[Show: Desktop with both browser tabs visible]**

> "Hello. I'm Praising Harris from IIIT Kottayam. This is PhantomGrid — a three-layer passive behavioural authentication engine built for Public Sector Banks. My teammates are Madapati Jyoti Radithya, who built the banking portal, and Kontheti Sai Akhilesh, who built the ML backend. I handled the analyst dashboard, security features, and integration tests.
>
> This is our Phase Two submission for CBI Hackathon 2026."

---

### [0:30 – 1:15] THE PROBLEM

**[Show: Stay on desktop, speak clearly]**

> "Let me start with the problem.
>
> Indian Public Sector Banks lost over seven thousand four hundred crore rupees to digital fraud in FY2023. Most of that didn't happen because hackers broke the system. It happened because they had the password.
>
> Current authentication checks who you are — once — at login. After that, the session is trusted completely. An attacker with stolen credentials walks straight in.
>
> OTPs help. But they are point-in-time gates. Once cleared, the session is open.
>
> PhantomGrid answers a different question: is the person currently operating this session the same person who enrolled? And it answers that question — continuously — on every transaction — with zero friction for the real user."

---

### [1:15 – 2:00] SYSTEM OVERVIEW

**[Show: Switch to dashboard tab at http://localhost:5599]**

> "This is the analyst dashboard. It polls the backend every two seconds and shows every live session in real time.
>
> The system has three independent behavioural layers.
>
> Layer One — CognitiveTrap. The banking portal has invisible decoy elements. A real customer who knows the interface never touches them. An attacker exploring an unfamiliar screen does.
>
> Layer Two — IntentTrace. How long do you spend on the beneficiary screen? How do you type the transfer amount? Legitimate users are habitual and fast. Attackers hesitate and read carefully.
>
> Layer Three — RhythmLock. When you type your PIN, the gaps between each keystroke — in milliseconds — are unique to you. That rhythm is your behavioural fingerprint.
>
> Each layer runs an independent ML model. The three scores are fused into one composite risk score. Below sixty — ALLOW. Sixty to seventy nine — OTP step-up. Eighty and above — BLOCK."

---

### [2:00 – 2:50] LEGITIMATE SESSION

**[Show: Switch to bank UI tab, or run demo_legit.py in terminal]**

**[Option A — script: type in terminal]**
```
python demo_legit.py
```

**[Option B — live bank UI: click Transfer, select beneficiary, type amount, type PIN, hit Pay]**

> "Let me show a genuine customer first.
>
> This is a real enrolled user. They navigate directly to the transfer screen — no hesitation, no decoy interactions. They type the amount naturally. And they enter their PIN — in their own rhythm, the same rhythm the system learned during enrollment.
>
> [pause 2 seconds while it processes]
>
> Composite score — two. Decision — ALLOW. The dashboard shows green. The transaction goes through. The customer never knew PhantomGrid was watching."

**[Show: Dashboard showing green ALLOW, gauge near 0]**

---

### [2:50 – 4:00] THE ATTACKER — MONEY SHOT

**[Switch to terminal, keep dashboard visible]**

> "Now — same account. Stolen credentials. And I want you to pay attention to something."

**[Pause. Speak slower here.]**

> "The attacker has the correct PIN."

**[Pause 1 second.]**

> "Watch what happens."

**[Type in terminal:]**
```
python demo_attacker.py
```

**[Watch dashboard — say nothing for 3 seconds while gauge moves]**

**[When BLOCK fires and red alert appears:]**

> "Composite score — one hundred. Decision — BLOCK."

**[Let the red screen sit. Pause 2 full seconds.]**

> "They tapped decoys. They hesitated on the beneficiary screen. And even though they typed the correct PIN digits — their rhythm was wrong. The gaps between keystrokes didn't match the enrolled baseline. RhythmLock caught it.
>
> The stolen PIN was not enough.
>
> Look at the WHY THIS DECISION panel on the dashboard. Layer One — high. Layer Two — high. Layer Three — high. Every layer flagged independently. There is no single point of bypass."

---

### [4:00 – 4:45] REPLAY ATTACK DEFENCE

**[Switch to terminal]**

> "Now, a more sophisticated attack. What if an attacker captures the legitimate user's network traffic — the exact JSON payload — and replays it verbatim? The behavioural data looks valid, because it IS the real user's data. It was just stolen off the wire."

**[Type:]**
```
python demo_replay.py
```

> "First call — scored normally, ALLOW. Now the attacker replays the exact same packet.
>
> [pause while it runs]
>
> Second call — BLOCK. replay detected equals true. Every verify call is SHA-256 signed. An exact duplicate within five minutes is detected by the audit service and forced to BLOCK. A captured session cannot be copy-pasted."

---

### [4:45 – 5:30] TAMPER-EVIDENT AUDIT TRAIL

**[Switch to terminal]**

> "One more. Every session PhantomGrid logs is hash-chained. Each row contains a SHA-256 hash of its own content, linked to the hash of the previous row. It's a cryptographic chain.
>
> Watch what happens when someone — an insider, a database admin — edits a row directly."

**[Type:]**
```
python verify_audit.py --tamper
```

> "The script mutates one row in the database directly. Then calls GET /audit/verify.
>
> [pause]
>
> The chain is broken at exactly that session. The dashboard audit badge flips from verified to tampered. We restore the record — chain is valid again.
>
> This is RBI-grade audit trail integrity. Any retrospective modification of any log record is detected instantly."

---

### [5:30 – 6:15] TEST SUITE + BENCHMARK

**[Switch to terminal]**

> "Everything you just saw is backed by a test suite."

**[Type:]**
```
pytest tests/ -v
```

> "Eight integration tests, running against the live backend right now. Each test uses an isolated user — no cross-test pollution. They cover: legitimate sessions scoring ALLOW, attackers scoring BLOCK, PIN rhythm mismatch detection, decoy tap flagging, order-independence of the scoring engine, fusion math across all decision bands, input validation, and session log persistence.
>
> [wait for 8 passed]
>
> Eight passed."

**[Switch to browser, open benchmark_report.html]**

> "And this is our benchmark — two hundred synthetic sessions, one hundred legitimate, one hundred attacker. Ninety-six point seven percent detection rate. Zero percent false positive rate. AUC one point zero. These are measured results, not claims."

---

### [6:15 – 7:00] CLOSING

**[Switch back to dashboard, show the full interface]**

> "To summarise what PhantomGrid delivers:
>
> Passive authentication — users do nothing differently.
>
> Continuous scoring — every transaction, not just login.
>
> Three independent ML models — Isolation Forest for behavioural anomaly, Dynamic Time Warping for keystroke rhythm.
>
> Replay-attack defence. Tamper-evident audit chain. Baseline maturity indicator. Explainability panel for every decision.
>
> And it integrates with any existing PSB banking portal via a single JavaScript file — no infrastructure changes, no hardware, no user training.
>
> For PSBs protecting five hundred million account holders — PhantomGrid is passive, invisible, and unbeatable.
>
> Thank you."

---

## DELIVERY NOTES

**Pace:** Slower than you think. Pause at every full stop.

**The BLOCK moment:** Say "Watch what happens." — then go completely silent while the gauge moves. Let the visual hit before you speak again.

**"The stolen PIN was not enough."** — say this after the pause, not before.

**Don't rush the audit section.** Judges need a second to read the output.

**If something goes wrong:** Don't restart. Just say "let me run that again" and continue. A small stumble is more authentic than a retake.

---

## EXACT COMMAND SEQUENCE (copy-paste ready)

```bash
# Terminal 1 (already running):
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Terminal 2 (already running):
cd dashboard
python -m http.server 5599

# Terminal 3 — run these during recording in order:
python demo_legit.py
python demo_attacker.py
python demo_replay.py
python verify_audit.py --tamper
pytest tests/ -v
```

---

*ZeroIntent_8_CBIHack2026 | Praising Y Harris Ratnam | Madapati Jyoti Radithya | Kontheti Sai Akhilesh*
