"""
tests/test_tracker.py
Unit tests untuk tools/tracker.py
Semua test menggunakan temp_db fixture — tidak ada side effect ke DB asli
"""

import pytest
import os
from datetime import datetime, timedelta


# ─── Setup ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def use_temp_db(temp_db):
    """Auto-use temp_db untuk setiap test di file ini."""
    yield


def get_tracker():
    """Import fresh setiap test agar DB_PATH ter-refresh."""
    import importlib
    import config
    import tools.tracker as t
    importlib.reload(config)
    importlib.reload(t)
    return t


# ─── track_application tests ────────────────────────────────────────────────

class TestTrackApplication:

    def test_create_new_application(self):
        t = get_tracker()
        result = t.track_application.invoke({
            "company": "Tokopedia",
            "role": "AI Engineer",
            "status": "email_drafted"
        })
        assert "created" in result
        assert "Tokopedia" in result
        assert "#1" in result

    def test_create_returns_id(self):
        t = get_tracker()
        result = t.track_application.invoke({
            "company": "Gojek",
            "role": "Backend Engineer"
        })
        assert "#" in result  # has ID

    def test_update_existing_application(self):
        t = get_tracker()
        # Create first
        t.track_application.invoke({"company": "Shopee", "role": "ML Engineer"})
        # Update same company+role
        result = t.track_application.invoke({
            "company": "Shopee",
            "role": "ML Engineer",
            "status": "sent",
            "notes": "Applied via email"
        })
        assert "updated" in result
        assert "sent" in result

    def test_case_insensitive_company_matching(self):
        t = get_tracker()
        t.track_application.invoke({"company": "tokopedia", "role": "AI Engineer"})
        result = t.track_application.invoke({"company": "TOKOPEDIA", "role": "AI Engineer", "status": "sent"})
        assert "updated" in result  # same record, not new

    def test_saves_email_draft(self):
        t = get_tracker()
        draft = "SUBJECT: Test\n\nHi, this is a test email."
        t.track_application.invoke({
            "company": "Bukalapak",
            "role": "Data Engineer",
            "email_draft": draft
        })
        app = t.get_application_by_id(1)
        assert app["email_draft"] == draft

    def test_invalid_status_returns_error(self):
        t = get_tracker()
        result = t.track_application.invoke({
            "company": "Test Corp",
            "role": "Engineer",
            "status": "invalid_status_xyz"
        })
        assert "Error" in result
        assert "Invalid status" in result

    def test_all_valid_statuses_accepted(self):
        from config import VALID_STATUSES
        t = get_tracker()
        for i, status in enumerate(VALID_STATUSES):
            result = t.track_application.invoke({
                "company": f"Company{i}",
                "role": "Engineer",
                "status": status
            })
            assert "Error" not in result, f"Status '{status}' should be valid"

    def test_multiple_companies_tracked_separately(self):
        t = get_tracker()
        t.track_application.invoke({"company": "A Corp", "role": "Engineer"})
        t.track_application.invoke({"company": "B Corp", "role": "Engineer"})
        t.track_application.invoke({"company": "C Corp", "role": "Engineer"})
        apps = t.get_all_applications()
        assert len(apps) == 3


# ─── check_followups tests ────────────────────────────────────────────────────

class TestCheckFollowups:

    def test_no_followups_when_empty(self):
        t = get_tracker()
        result = t.check_followups.invoke({"days_threshold": 7})
        assert "No applications" in result

    def test_no_followups_when_status_not_sent(self):
        t = get_tracker()
        t.track_application.invoke({"company": "X", "role": "Dev", "status": "email_drafted"})
        result = t.check_followups.invoke({"days_threshold": 7})
        assert "No applications" in result  # drafted, not sent

    def test_detects_stale_sent_application(self, temp_db):
        """Manually insert stale record to simulate old application."""
        import sqlite3
        stale_date = (datetime.now() - timedelta(days=10)).isoformat()
        t = get_tracker()
        conn = sqlite3.connect(temp_db)
        t._ensure_tables(conn)
        conn.execute("""
            INSERT INTO applications (company, role, status, last_action, applied_at)
            VALUES ('OldCo', 'Dev', 'sent', ?, ?)
        """, (stale_date, stale_date))
        conn.commit()
        conn.close()

        t = get_tracker()
        result = t.check_followups.invoke({"days_threshold": 7})
        assert "OldCo" in result
        assert "need follow-up" in result

    def test_does_not_flag_recent_sent(self, temp_db):
        """Application sent 2 days ago should NOT be flagged with 7-day threshold."""
        import sqlite3
        recent_date = (datetime.now() - timedelta(days=2)).isoformat()
        t = get_tracker()
        conn = sqlite3.connect(temp_db)
        t._ensure_tables(conn)
        conn.execute("""
            INSERT INTO applications (company, role, status, last_action, applied_at)
            VALUES ('NewCo', 'Dev', 'sent', ?, ?)
        """, (recent_date, recent_date))
        conn.commit()
        conn.close()

        t = get_tracker()
        result = t.check_followups.invoke({"days_threshold": 7})
        assert "No applications" in result

    def test_custom_threshold(self, temp_db):
        """Test with 3-day threshold instead of default 7."""
        import sqlite3
        date_5_days_ago = (datetime.now() - timedelta(days=5)).isoformat()
        t = get_tracker()
        conn = sqlite3.connect(temp_db)
        t._ensure_tables(conn)
        conn.execute("""
            INSERT INTO applications (company, role, status, last_action, applied_at)
            VALUES ('MidCo', 'Dev', 'sent', ?, ?)
        """, (date_5_days_ago, date_5_days_ago))
        conn.commit()
        conn.close()

        t = get_tracker()
        result_7 = t.check_followups.invoke({"days_threshold": 7})
        result_3 = t.check_followups.invoke({"days_threshold": 3})

        assert "No applications" in result_7   # 5 days < 7 threshold → not flagged
        assert "MidCo" in result_3              # 5 days > 3 threshold → flagged


# ─── update_application_status tests ─────────────────────────────────────────

class TestUpdateStatus:

    def test_update_existing(self):
        t = get_tracker()
        t.track_application.invoke({"company": "Tes Inc", "role": "Dev", "status": "email_drafted"})
        result = t.update_application_status.invoke({
            "company": "Tes Inc",
            "role": "Dev",
            "new_status": "sent"
        })
        assert "Updated" in result
        assert "sent" in result

    def test_update_nonexistent_returns_error(self):
        t = get_tracker()
        result = t.update_application_status.invoke({
            "company": "Ghost Corp",
            "role": "Dev",
            "new_status": "sent"
        })
        assert "Error" in result
        assert "No application found" in result

    def test_invalid_new_status_returns_error(self):
        t = get_tracker()
        result = t.update_application_status.invoke({
            "company": "Any",
            "role": "Any",
            "new_status": "hired"  # not a valid status
        })
        assert "Error" in result


# ─── Helper function tests ────────────────────────────────────────────────────

class TestHelpers:

    def test_get_all_applications_empty(self):
        t = get_tracker()
        apps = t.get_all_applications()
        assert apps == []

    def test_get_all_applications_returns_list(self):
        t = get_tracker()
        t.track_application.invoke({"company": "A", "role": "Dev"})
        t.track_application.invoke({"company": "B", "role": "Dev"})
        apps = t.get_all_applications()
        assert len(apps) == 2
        assert isinstance(apps[0], dict)

    def test_get_application_by_id(self):
        t = get_tracker()
        t.track_application.invoke({"company": "FindMe", "role": "Engineer"})
        app = t.get_application_by_id(1)
        assert app is not None
        assert app["company"] == "FindMe"

    def test_get_application_by_id_not_found(self):
        t = get_tracker()
        app = t.get_application_by_id(9999)
        assert app is None

    def test_delete_application(self):
        t = get_tracker()
        t.track_application.invoke({"company": "Delete Me", "role": "Dev"})
        deleted = t.delete_application(1)
        assert deleted is True
        assert t.get_application_by_id(1) is None

    def test_delete_nonexistent(self):
        t = get_tracker()
        deleted = t.delete_application(9999)
        assert deleted is False

    def test_get_stats_empty(self):
        t = get_tracker()
        stats = t.get_stats()
        assert stats["total"] == 0
        assert all(v == 0 for v in stats["by_status"].values())

    def test_get_stats_counts(self):
        t = get_tracker()
        t.track_application.invoke({"company": "A", "role": "Dev", "status": "email_drafted"})
        t.track_application.invoke({"company": "B", "role": "Dev", "status": "sent"})
        t.track_application.invoke({"company": "C", "role": "Dev", "status": "sent"})
        stats = t.get_stats()
        assert stats["total"] == 3
        assert stats["by_status"]["email_drafted"] == 1
        assert stats["by_status"]["sent"] == 2

    def test_export_to_csv_empty(self):
        t = get_tracker()
        result = t.export_to_csv()
        assert result == ""

    def test_export_to_csv_has_header(self):
        t = get_tracker()
        t.track_application.invoke({"company": "CSV Corp", "role": "Dev"})
        csv_str = t.export_to_csv()
        assert "company" in csv_str
        assert "CSV Corp" in csv_str
