"""
PhantomGrid — Audit-trail integrity verifier (tamper-evidence demo).

Walks the hash-chained session_logs and reports integrity. Pass --tamper to
demonstrate detection: it flips one row in the DB, re-checks (FAIL), then
restores it.

    python verify_audit.py
    python verify_audit.py --tamper
"""

import sys
import sqlite3
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from config import BASE_URL
except Exception:
    BASE_URL = "http://127.0.0.1:8000"

DB = r"C:\Users\LENOVO\OneDrive\Desktop\PhantomGrid\backend\phantomgrid.db"


def check():
    return requests.get(f"{BASE_URL}/audit/verify", timeout=10).json()


def main():
    print(f"\n  PhantomGrid — AUDIT INTEGRITY   (backend: {BASE_URL})\n")
    r = check()
    print(f"   chain: {'VALID ✓' if r['valid'] else 'TAMPERED ✗'}  "
          f"(verified {r['verified']}/{r['total']})")

    if "--tamper" in sys.argv:
        print("\n   >>> Tampering with one row directly in the database...")
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("SELECT id, composite_score FROM session_logs ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if not row:
            print("   (no rows to tamper — run a session first)"); con.close(); return
        rid, old = row
        cur.execute("UPDATE session_logs SET composite_score=? WHERE id=?", (old + 5, rid))
        con.commit()
        r2 = check()
        print(f"   re-check: {'VALID ✓' if r2['valid'] else 'TAMPERED ✗'}  "
              f"-> broken at session {r2['broken_at_session']}")
        cur.execute("UPDATE session_logs SET composite_score=? WHERE id=?", (old, rid))
        con.commit(); con.close()
        r3 = check()
        print(f"   restored: {'VALID ✓' if r3['valid'] else 'still broken'}")
        print("\n   🛡 Any edit to any row is detected — tamper-evident audit trail.\n")
    else:
        print()


if __name__ == "__main__":
    main()
