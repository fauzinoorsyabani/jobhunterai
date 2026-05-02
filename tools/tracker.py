"""
tools/tracker.py
Database layer: SQLite CRUD untuk job applications
Tools: track_application, check_followups, update_application_status
Helpers: get_all_applications, get_stats, delete_application
"""

import sqlite3
import json
from datetime import datetime, timedelta
from langchain_core.tools import tool
from config import DB_PATH, VALID_STATUSES, FOLLOWUP_THRESHOLD_DAYS


# ─── Database Setup ──────────────────────────────────────────────────────────

def _get_conn(db_path: str = None) -> sqlite3.Connection:
    """Get SQLite connection. db_path override untuk testing."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection):
    """Create tables if not exist. Safe to call multiple times."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            company         TEXT NOT NULL,
            role            TEXT NOT NULL,
            status          TEXT DEFAULT 'email_drafted',
            email_draft     TEXT DEFAULT '',
            applied_at      TEXT DEFAULT (datetime('now')),
            last_action     TEXT DEFAULT (datetime('now')),
            notes           TEXT DEFAULT '',
            contact_name    TEXT DEFAULT '',
            contact_email   TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS user_profile (
            id          INTEGER PRIMARY KEY CHECK (id = 1),
            name        TEXT DEFAULT '',
            skills      TEXT DEFAULT '[]',
            experience  TEXT DEFAULT '',
            target_role TEXT DEFAULT '',
            updated_at  TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


# ─── LangChain Tools ─────────────────────────────────────────────────────────

@tool
def track_application(
    company: str,
    role: str,
    status: str = "email_drafted",
    email_draft: str = "",
    notes: str = "",
    contact_name: str = "",
    contact_email: str = ""
) -> str:
    """
    Save or update a job application in the database.
    Call this AFTER drafting an email, or when application status changes.

    Args:
        company: Company name (e.g., "Tokopedia")
        role: Job role (e.g., "AI Engineer")
        status: One of: email_drafted, sent, replied, interview_scheduled,
                interview_done, offer_received, rejected, withdrawn
        email_draft: The full email content that was drafted
        notes: Additional notes about this application
        contact_name: Hiring manager or recruiter name if known
        contact_email: Hiring manager email if known

    Returns:
        Confirmation message with application ID and current status
    """
    # Validate status
    if status not in VALID_STATUSES:
        return f"Error: Invalid status '{status}'. Valid options: {', '.join(VALID_STATUSES)}"

    conn = _get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM applications WHERE LOWER(company)=LOWER(?) AND LOWER(role)=LOWER(?)",
            (company, role)
        ).fetchone()

        now = datetime.now().isoformat()

        if existing:
            conn.execute("""
                UPDATE applications
                SET status=?, email_draft=?, last_action=?, notes=?,
                    contact_name=?, contact_email=?
                WHERE id=?
            """, (status, email_draft, now, notes, contact_name, contact_email, existing["id"]))
            app_id = existing["id"]
            action = "updated"
        else:
            cur = conn.execute("""
                INSERT INTO applications
                    (company, role, status, email_draft, notes, contact_name, contact_email, applied_at, last_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (company, role, status, email_draft, notes, contact_name, contact_email, now, now))
            app_id = cur.lastrowid
            action = "created"

        conn.commit()
        return f"✓ Application #{app_id} {action}: {company} — {role} [{status}]"

    finally:
        conn.close()


@tool
def check_followups(days_threshold: int = 7) -> str:
    """
    Find applications that need a follow-up email.
    Flags applications with status 'sent' that have had no activity for N days.

    Args:
        days_threshold: Days without activity before flagging (default: 7)

    Returns:
        List of applications needing follow-up, or confirmation that none needed.
    """
    conn = _get_conn()
    try:
        cutoff = (datetime.now() - timedelta(days=days_threshold)).isoformat()
        rows = conn.execute("""
            SELECT id, company, role, last_action, status
            FROM applications
            WHERE status = 'sent' AND last_action < ?
            ORDER BY last_action ASC
        """, (cutoff,)).fetchall()

        if not rows:
            return f"✓ No applications need follow-up (threshold: {days_threshold} days)."

        lines = [f"⚠️  {len(rows)} application(s) need follow-up:\n"]
        for r in rows:
            try:
                last = datetime.fromisoformat(r["last_action"])
                days_ago = (datetime.now() - last).days
            except Exception:
                days_ago = "?"

            lines.append(
                f"• #{r['id']} {r['company']} ({r['role']}) — "
                f"sent {days_ago} day(s) ago, no reply yet"
            )

        lines.append(
            "\n💡 Suggested action: Send a brief 2-3 sentence follow-up "
            "referencing your original email. Keep it friendly, not pushy."
        )
        return "\n".join(lines)

    finally:
        conn.close()


@tool
def update_application_status(company: str, role: str, new_status: str) -> str:
    """
    Update the status of an existing job application.

    Args:
        company: Company name of the application to update
        role: Job role of the application to update
        new_status: New status (email_drafted/sent/replied/interview_scheduled/
                    interview_done/offer_received/rejected/withdrawn)

    Returns:
        Confirmation or error message
    """
    if new_status not in VALID_STATUSES:
        return f"Error: Invalid status '{new_status}'. Choose from: {', '.join(VALID_STATUSES)}"

    conn = _get_conn()
    try:
        cur = conn.execute("""
            UPDATE applications
            SET status=?, last_action=datetime('now')
            WHERE LOWER(company)=LOWER(?) AND LOWER(role)=LOWER(?)
        """, (new_status, company, role))
        conn.commit()

        if cur.rowcount == 0:
            return f"Error: No application found for {company} — {role}"

        return f"✓ Updated {company} ({role}) → [{new_status}]"

    finally:
        conn.close()


# ─── Helper Functions (untuk UI, bukan tool) ─────────────────────────────────

def get_all_applications() -> list[dict]:
    """Return all applications sorted by most recent first."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY applied_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_application_by_id(app_id: int) -> dict | None:
    """Return single application by ID, or None if not found."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM applications WHERE id=?", (app_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_application(app_id: int) -> bool:
    """Delete application by ID. Returns True if deleted, False if not found."""
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM applications WHERE id=?", (app_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_stats() -> dict:
    """Return counts: total applications and breakdown by status."""
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        by_status = {}
        for status in VALID_STATUSES:
            count = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE status=?", (status,)
            ).fetchone()[0]
            by_status[status] = count
        return {"total": total, "by_status": by_status}
    finally:
        conn.close()


def export_to_csv() -> str:
    """Export all applications to CSV string."""
    import csv
    import io

    apps = get_all_applications()
    if not apps:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=apps[0].keys())
    writer.writeheader()
    writer.writerows(apps)
    return output.getvalue()
