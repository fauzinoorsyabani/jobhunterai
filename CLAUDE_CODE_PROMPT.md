User minta "mendetail lengkap" — ini override token protocol. Gas full detail:


Master Claude Code prompt - Groq version with GitHub workflow, unit tests, deploy loop
Master Claude Code prompt - Groq version with GitHub workflow, unit tests, deploy loop

Master Claude Code prompt - Groq version with GitHub workflow, unit tests, deploy loop
markdown

# ============================================================
# CLAUDE CODE MASTER PROMPT — JobHunterAI Agent
# Stack: Groq (FREE) + Tavily (FREE) + LangGraph + Streamlit
# Workflow: GitHub-first, issue per fase, commit per fitur
# ============================================================
#
# CARA PAKAI:
# 1. Paste SELURUH prompt ini ke Claude Code sekali di awal
# 2. Claude Code akan loop otomatis fase per fase
# 3. Setiap fase: code → test → push → buat GitHub issue next fase
# 4. Kalau ada yang salah: cek GitHub, revert, lanjut
#
# ============================================================

---

## 🧠 IDENTITAS & MISI

Kamu adalah senior AI engineer yang build JobHunterAI dari nol.
Kamu bekerja dalam loop: **code → test → commit → push → issue → repeat**.
Tidak ada fase yang dianggap selesai tanpa:
1. Semua unit test PASS
2. Code ter-push ke GitHub
3. GitHub Issue untuk fase berikutnya sudah dibuat

Jika test gagal → fix → test lagi. Jangan lanjut ke fase berikutnya sampai test PASS.

---

## 📦 PROJECT OVERVIEW

**JobHunterAI** = AI Agent yang otomatis:
1. Riset perusahaan target (Tavily API — gratis)
2. Tulis cold email personal (Groq Llama 3.3 70B — gratis)
3. Track semua lamaran di database lokal (SQLite)
4. Deteksi lamaran yang butuh follow-up
5. Analisis job market + skill gap

**Stack lengkap:**
- LangGraph 0.2+ (agentic loop)
- langchain-groq (LLM provider, GRATIS)
- langchain-google-genai (fallback LLM, GRATIS)
- tavily-python (web search, GRATIS 1000 req/bulan)
- SQLite (database lokal, no setup needed)
- Streamlit (UI)
- pytest + pytest-mock (testing)
- GitHub Actions (CI/CD)
- Railway (deploy, free tier)

**API Keys yang dibutuhkan (semua GRATIS):**
- GROQ_API_KEY → console.groq.com (daftar pakai GitHub)
- GOOGLE_API_KEY → aistudio.google.com (backup LLM)
- TAVILY_API_KEY → tavily.com

---

## 🔧 SETUP AWAL (JALANKAN SEKALI SEBELUM SEMUA FASE)

### Step 1: Inisialisasi Git + GitHub

```bash
# Di terminal, jalankan ini satu per satu:
cd ~/
mkdir jobhunterai && cd jobhunterai
git init
git branch -M main

# Buat repo di GitHub via CLI (install gh dulu jika belum)
# Atau buat manual di github.com lalu:
git remote add origin https://github.com/USERNAME/jobhunterai.git
```

### Step 2: Buat struktur folder

```bash
mkdir -p tools tests ui .streamlit .github/workflows
touch tools/__init__.py tests/__init__.py
```

Struktur akhir yang dituju:
```
jobhunterai/
├── .github/
│   └── workflows/
│       └── ci.yml              ← GitHub Actions CI
├── .streamlit/
│   └── config.toml             ← Streamlit theme
├── tools/
│   ├── __init__.py
│   ├── research.py             ← Tool 1: Company Research
│   ├── email.py                ← Tool 2: Email Writer
│   ├── tracker.py              ← Tool 3 & 4: Tracker + Followup
│   └── market.py               ← Tool 5: Market Analyzer
├── tests/
│   ├── __init__.py
│   ├── conftest.py             ← Shared fixtures & mocks
│   ├── test_tracker.py
│   ├── test_research.py
│   ├── test_email.py
│   ├── test_market.py
│   └── test_agent.py
├── ui/
│   └── app.py                  ← Streamlit UI
├── agent.py                    ← LangGraph agent core
├── config.py                   ← Centralized config
├── requirements.txt
├── requirements-dev.txt        ← Dev dependencies (pytest dll)
├── Procfile                    ← Railway deploy
├── railway.json
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

### Step 3: Buat file konfigurasi global

**config.py** — satu tempat semua config, tidak ada hardcode di tools:
```python
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Config
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# Model selection
MODEL_FAST = "llama-3.3-70b-versatile"      # Groq — untuk research, market
MODEL_QUALITY = "llama-3.3-70b-versatile"   # Groq — untuk email (sama, tapi prompt lebih ketat)
MODEL_FALLBACK = "gemini-2.0-flash"         # Google — jika Groq rate limit

# Database
DB_PATH = os.environ.get("DB_PATH", "jobhunter.db")

# Tavily
TAVILY_MAX_RESULTS = 5
TAVILY_SEARCH_DEPTH = "basic"  # "basic" hemat quota, "advanced" lebih detail

# Agent
MAX_AGENT_ITERATIONS = 10  # batas loop agent agar tidak infinite
FOLLOWUP_THRESHOLD_DAYS = 7

# Valid application statuses
VALID_STATUSES = [
    "email_drafted",
    "sent",
    "replied",
    "interview_scheduled",
    "interview_done",
    "offer_received",
    "rejected",
    "withdrawn"
]
```

**requirements.txt:**
```
langgraph==0.2.55
langchain-core==0.3.29
langchain-groq==0.2.3
langchain-google-genai==2.1.0
tavily-python==0.5.0
streamlit==1.40.0
python-dotenv==1.0.0
```

**requirements-dev.txt:**
```
-r requirements.txt
pytest==8.3.0
pytest-asyncio==0.24.0
pytest-mock==3.14.0
pytest-cov==6.0.0
ruff==0.8.0
black==24.10.0
```

**.env.example:**
```
# LLM (pilih salah satu atau keduanya untuk fallback)
GROQ_API_KEY=gsk_...          # console.groq.com — GRATIS
GOOGLE_API_KEY=AIza...        # aistudio.google.com — GRATIS

# Search
TAVILY_API_KEY=tvly-...       # tavily.com — GRATIS 1000 req/bulan

# Database (opsional, default: jobhunter.db di root)
DB_PATH=jobhunter.db
```

**.gitignore:**
```
venv/
__pycache__/
*.pyc
*.pyo
.env
*.db
*.sqlite3
.streamlit/secrets.toml
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage
dist/
build/
*.egg-info/
```

**tests/conftest.py** — shared fixtures untuk semua test:
```python
import pytest
import os
import tempfile

# Set dummy env vars SEBELUM import apapun
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")

@pytest.fixture
def temp_db(tmp_path):
    """Temporary SQLite database for each test — isolated, no cleanup needed."""
    db_file = str(tmp_path / "test_jobhunter.db")
    os.environ["DB_PATH"] = db_file
    yield db_file
    # tmp_path auto-cleanup by pytest

@pytest.fixture
def sample_user_profile():
    return {
        "name": "Budi Santoso",
        "skills": ["Python", "FastAPI", "LangChain", "SQL", "Docker"],
        "experience": "Semester 8 CS, 6-month fintech internship",
        "target_role": "AI Engineer"
    }

@pytest.fixture
def sample_company_research():
    return """## Tokopedia Research

**What they do:** Indonesia's largest e-commerce platform, part of GoTo Group.
**Tech stack:** Python, Kubernetes, Kafka, PostgreSQL, TensorFlow, LLM infra team.
**Recent news:** Expanding AI-powered product recommendations, hiring ML engineers aggressively in 2025.
**Culture signals:** Fast-paced, engineering-first culture. Strong open source contributions.
**Why apply:** Active LLM team expansion, direct impact on 100M+ users."""

@pytest.fixture
def mock_groq_response(mocker):
    """Mock Groq LLM response to avoid real API calls."""
    mock = mocker.patch("langchain_groq.ChatGroq.invoke")
    mock.return_value.content = "Mocked LLM response"
    return mock

@pytest.fixture
def mock_tavily(mocker):
    """Mock Tavily search to avoid real API calls."""
    mock = mocker.patch("tavily.TavilyClient.search")
    mock.return_value = {
        "results": [
            {"title": "Tokopedia Engineering Blog", "content": "Tokopedia uses Python, Kubernetes, and ML at scale.", "url": "https://example.com"},
            {"title": "Tokopedia Hiring 2025", "content": "Tokopedia is hiring AI engineers for LLM team.", "url": "https://example.com/2"},
        ]
    }
    return mock
```

**GitHub Actions CI (.github/workflows/ci.yml):**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Lint with ruff
        run: ruff check . --output-format=github
      
      - name: Run unit tests
        env:
          GROQ_API_KEY: test-key
          GOOGLE_API_KEY: test-key
          TAVILY_API_KEY: test-key
        run: |
          pytest tests/ -v --tb=short --cov=. --cov-report=xml \
            -m "not integration" \
            --ignore=tests/test_agent.py
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
        continue-on-error: true  # jangan gagalkan CI karena coverage upload
```

### Step 4: Commit awal

```bash
git add .
git commit -m "chore: initial project structure and config"
git push -u origin main
```

### Step 5: Buat GitHub Issues untuk semua fase

Jalankan script ini (butuh `gh` CLI terinstall):
```bash
gh issue create --title "Fase 1: Database Layer (tracker.py)" \
  --body "Implement SQLite CRUD, track_application, check_followups, update_status tools. All unit tests must pass." \
  --label "enhancement"

gh issue create --title "Fase 2: Company Research Tool (research.py)" \
  --body "Implement Tavily search + Groq summarization. Unit tests with mocked API." \
  --label "enhancement"

gh issue create --title "Fase 3: Email Writer Tool (email.py)" \
  --body "Implement personalized cold email writer using Groq. Validation logic included." \
  --label "enhancement"

gh issue create --title "Fase 4: Market Analyzer Tool (market.py)" \
  --body "Implement skill gap analysis and salary range lookup." \
  --label "enhancement"

gh issue create --title "Fase 5: LangGraph Agent Core (agent.py)" \
  --body "Implement StateGraph, tool routing, MemorySaver, streaming support." \
  --label "enhancement"

gh issue create --title "Fase 6: Streamlit UI (ui/app.py)" \
  --body "Build production-ready chat UI with tracker panel and stats sidebar." \
  --label "enhancement"

gh issue create --title "Fase 7: Deploy to Railway" \
  --body "Procfile, Dockerfile, railway.json, env vars setup, health check." \
  --label "deployment"
```

Atau buat manual di github.com/USERNAME/jobhunterai/issues

---

## 🔁 LOOP PROTOCOL (IKUTI SETIAP FASE)

Setiap fase mengikuti loop ini TANPA PENGECUALIAN:

```
┌─────────────────────────────────────┐
│  START FASE N                       │
│  1. Buka GitHub Issue #N            │
│  2. Buat branch: git checkout -b    │
│     feat/fase-N-nama                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  IMPLEMENT                          │
│  - Tulis kode sesuai spec           │
│  - Tulis unit test                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  TEST LOOP                          │
│  pytest tests/test_NAMA.py -v       │
│       │                             │
│  FAIL ◄──── fix code ───► PASS      │
│                              │      │
└──────────────────────────────┼──────┘
                               │
                               ▼
┌─────────────────────────────────────┐
│  COMMIT & PUSH                      │
│  git add .                          │
│  git commit -m "feat: ..."          │
│  git push origin feat/fase-N-nama   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  MERGE & CLOSE ISSUE                │
│  gh pr create --fill                │
│  gh pr merge --squash               │
│  gh issue close N                   │
│  git checkout main && git pull      │
└──────────────┬──────────────────────┘
               │
               ▼
         MULAI FASE N+1
```

**Commit message convention:**
```
feat: tambah fitur baru
fix: perbaikan bug
test: tambah/update test
chore: setup, config, deps
refactor: ubah struktur tanpa ganti behavior
docs: update README/komentar
```

---

## FASE 1 — DATABASE LAYER

**GitHub Issue:** #1 "Fase 1: Database Layer (tracker.py)"
**Branch:** `feat/fase-1-database`

### Implementasi tools/tracker.py (lengkap):

```python
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
```

### Implementasi tests/test_tracker.py (lengkap):

```python
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
    import tools.tracker as t
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
        conn = sqlite3.connect(temp_db)
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
        conn = sqlite3.connect(temp_db)
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
        conn = sqlite3.connect(temp_db)
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
```

### Command setelah selesai:

```bash
# Jalankan test
pytest tests/test_tracker.py -v --tb=short

# Jika semua pass:
git checkout -b feat/fase-1-database
git add tools/tracker.py tests/test_tracker.py config.py
git commit -m "feat: add database layer with SQLite tracker tools"
git push origin feat/fase-1-database

# Buat PR dan merge
gh pr create --title "feat: database layer" --body "Closes #1" --base main
gh pr merge --squash
git checkout main && git pull

# Close issue
gh issue close 1 --comment "All tracker tests passing ✓"
```

---

## FASE 2 — COMPANY RESEARCH TOOL

**GitHub Issue:** #2
**Branch:** `feat/fase-2-research`

### Implementasi tools/research.py:

```python
"""
tools/research.py
Tool: company_research
Menggunakan Tavily untuk web search + Groq untuk summarization
"""

import time
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from tavily import TavilyClient
from config import GROQ_API_KEY, TAVILY_API_KEY, MODEL_FAST, TAVILY_MAX_RESULTS

# In-memory cache {company_lower: (timestamp, result)}
_cache: dict[str, tuple[float, str]] = {}
CACHE_TTL_SECONDS = 3600  # 1 jam


def _get_llm():
    return ChatGroq(model=MODEL_FAST, api_key=GROQ_API_KEY, temperature=0.3)


def _get_tavily():
    return TavilyClient(api_key=TAVILY_API_KEY)


def _search_company(company_name: str) -> list[dict]:
    """Run 3 Tavily queries, deduplicate by URL, return top snippets."""
    client = _get_tavily()
    queries = [
        f"{company_name} technology stack engineering team 2025",
        f"{company_name} company news product launch 2024 2025",
        f"{company_name} work culture employee review glassdoor",
    ]

    seen_urls = set()
    snippets = []

    for q in queries:
        try:
            resp = client.search(q, max_results=TAVILY_MAX_RESULTS, search_depth="basic")
            for r in resp.get("results", []):
                url = r.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    snippets.append({
                        "title": r.get("title", ""),
                        "content": r.get("content", "")[:400],
                        "url": url,
                    })
        except Exception:
            continue  # Skip failed queries, jangan crash

    return snippets[:12]  # cap 12 snippets ke LLM


def _summarize(company_name: str, snippets: list[dict]) -> str:
    """Summarize raw snippets into structured markdown."""
    if not snippets:
        return f"Limited information found for **{company_name}**. Proceed with general knowledge."

    raw = "\n".join([f"- {s['title']}: {s['content']}" for s in snippets])
    llm = _get_llm()

    prompt = f"""You are helping a job applicant research {company_name} before writing a cold email.

Summarize this raw data into a structured markdown report. Be specific and factual.

Raw data:
{raw}

Output format (use exactly this structure):
## {company_name}

**What they do:** [1-2 sentence description]

**Tech stack:** [bullet list of technologies mentioned]

**Recent highlights:** [2-3 bullet points of recent news/launches]

**Culture signals:** [1-2 bullet points from reviews/press]

**Hook for email:** [1 sentence — a specific, compelling reason to mention in a cold email]

Keep total output under 300 words. Only include facts from the data provided."""

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Research summary unavailable for {company_name}. Error: {str(e)}"


@tool
def company_research(company_name: str) -> str:
    """
    Research a company's tech stack, culture, and recent news.
    Use this tool BEFORE writing any cold email.

    Args:
        company_name: Name of the company to research (e.g., "Tokopedia", "Gojek")

    Returns:
        Structured markdown summary: what they do, tech stack, news, culture, email hook
    """
    cache_key = company_name.lower().strip()

    # Check cache
    if cache_key in _cache:
        cached_time, cached_result = _cache[cache_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return f"[cached] {cached_result}"

    # Fetch + summarize
    snippets = _search_company(company_name)
    result = _summarize(company_name, snippets)

    # Store in cache
    _cache[cache_key] = (time.time(), result)

    return result
```

### tests/test_research.py:

```python
"""tests/test_research.py"""

import pytest


class TestCompanyResearch:

    def test_returns_string(self, mock_tavily, mock_groq_response):
        from tools.research import company_research
        result = company_research.invoke({"company_name": "Google"})
        assert isinstance(result, str)
        assert len(result) > 10

    def test_uses_company_name_in_output(self, mock_tavily, mock_groq_response):
        from tools.research import company_research
        mock_groq_response.return_value.content = "## TestCorp\n**What they do:** Testing things."
        result = company_research.invoke({"company_name": "TestCorp"})
        assert isinstance(result, str)

    def test_handles_tavily_failure_gracefully(self, mocker, mock_groq_response):
        """Jika Tavily gagal, harus return string, bukan crash."""
        mocker.patch("tavily.TavilyClient.search", side_effect=Exception("API Error"))
        from tools.research import company_research
        result = company_research.invoke({"company_name": "UnknownXYZ"})
        assert isinstance(result, str)
        assert len(result) > 0  # tidak crash, return sesuatu

    def test_handles_groq_failure_gracefully(self, mock_tavily, mocker):
        """Jika Groq gagal, harus return string, bukan crash."""
        mocker.patch("langchain_groq.ChatGroq.invoke", side_effect=Exception("Rate limit"))
        from tools.research import company_research
        result = company_research.invoke({"company_name": "SomeCompany"})
        assert isinstance(result, str)

    def test_caching_second_call_faster(self, mock_tavily, mock_groq_response):
        """Second call untuk company sama harus pakai cache."""
        import time
        from tools.research import company_research, _cache
        _cache.clear()

        company_research.invoke({"company_name": "CacheTest Inc"})
        mock_tavily.reset_mock()

        company_research.invoke({"company_name": "CacheTest Inc"})

        # Tavily should NOT be called second time (cached)
        mock_tavily.assert_not_called()

    def test_empty_snippets_returns_graceful_message(self, mocker, mock_groq_response):
        """Jika Tavily return empty, harus ada pesan fallback."""
        mocker.patch("tavily.TavilyClient.search", return_value={"results": []})
        from tools.research import company_research
        result = company_research.invoke({"company_name": "NoInfoCorp"})
        assert isinstance(result, str)
```

```bash
pytest tests/test_research.py -v --tb=short
# Semua pass → commit → push → close issue #2
```

---

## FASE 3 — EMAIL WRITER TOOL

**GitHub Issue:** #3
**Branch:** `feat/fase-3-email`

### Implementasi tools/email.py:

```python
"""
tools/email.py
Tool: email_writer
Generates personalized cold emails using Groq LLM
Includes validation: subject check, word count, banned phrases
"""

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_QUALITY

BANNED_PHRASES = [
    "i am writing to express my interest",
    "passionate about",
    "team player",
    "fast learner",
    "i look forward to hearing from you",
    "to whom it may concern",
    "please find attached",
    "i believe i would be a great fit",
]

MAX_WORDS = 200  # hard limit, give 50-word buffer over 150 target


def _get_llm():
    return ChatGroq(model=MODEL_QUALITY, api_key=GROQ_API_KEY, temperature=0.7)


def _validate_email(email_text: str) -> tuple[bool, str]:
    """
    Validate generated email.
    Returns (is_valid, reason_if_invalid)
    """
    if not email_text.startswith("SUBJECT:"):
        return False, "Missing SUBJECT: prefix"

    # Count body words (everything after first blank line)
    parts = email_text.split("\n\n", 1)
    if len(parts) < 2:
        return False, "No email body found"

    body = parts[1]
    word_count = len(body.split())
    if word_count > MAX_WORDS:
        return False, f"Body too long: {word_count} words (max {MAX_WORDS})"

    lower_body = body.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lower_body:
            return False, f"Contains banned phrase: '{phrase}'"

    return True, ""


def _build_prompt(company_name, role, research_summary, user_profile, tone) -> str:
    tone_instructions = {
        "professional": "Formal, data-driven, concise. No casual language.",
        "casual": "Friendly and conversational, but still competent and clear.",
        "bold": "Direct, confident opener. Make a strong statement upfront. Confident ask.",
    }.get(tone, "Professional tone.")

    return f"""You are an expert cold email writer for tech job applications in Indonesia.

STRICT RULES:
- Output MUST start with: SUBJECT: [specific subject line]
- Subject line must mention the role AND one specific thing about the company
- Body must be under 150 words
- Opening line must NOT be "I am writing to express my interest"
- Reference AT LEAST 1 specific fact from the company research below
- Mention AT LEAST 1 concrete skill or achievement from the applicant profile
- CTA must offer a 15-minute call or video chat — not "I look forward to hearing from you"
- Tone: {tone_instructions}
- NEVER use these phrases: {", ".join(BANNED_PHRASES[:4])}

COMPANY RESEARCH:
{research_summary}

APPLICANT PROFILE:
{user_profile}

TARGET ROLE: {role} at {company_name}

Write the email now. Format:
SUBJECT: [subject line]

[email body — max 150 words]"""


@tool
def email_writer(
    company_name: str,
    role: str,
    company_research_summary: str,
    user_profile: str,
    tone: str = "professional"
) -> str:
    """
    Write a personalized cold email for a job application.
    ALWAYS call company_research first and pass its output as company_research_summary.

    Args:
        company_name: Target company name
        role: Job role being applied for
        company_research_summary: Output from company_research tool (required)
        user_profile: Applicant's background as a string (name, skills, experience)
        tone: "professional" | "casual" | "bold"

    Returns:
        SUBJECT line + email body, formatted and ready to copy-paste
    """
    if tone not in ("professional", "casual", "bold"):
        tone = "professional"

    llm = _get_llm()
    prompt = _build_prompt(company_name, role, company_research_summary, user_profile, tone)

    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            response = llm.invoke(prompt)
            email_text = response.content.strip()

            is_valid, reason = _validate_email(email_text)
            if is_valid:
                return email_text

            # If invalid, add reminder and retry once
            if attempt < max_attempts - 1:
                prompt += f"\n\nPREVIOUS ATTEMPT FAILED: {reason}. Fix this and try again."

        except Exception as e:
            if attempt == max_attempts - 1:
                return f"Error generating email: {str(e)}"

    return email_text  # return best attempt even if validation failed
```

### tests/test_email.py:

```python
"""tests/test_email.py"""

import pytest


class TestEmailValidation:
    """Test _validate_email function directly."""

    def _validate(self, text):
        from tools.email import _validate_email
        return _validate_email(text)

    def test_valid_email_passes(self):
        email = "SUBJECT: AI Engineer @ Tokopedia — LangGraph experience\n\nHi team, saw your LLM initiative. I built a RAG system reducing query latency by 40%. Open to a 15-min call?"
        valid, reason = self._validate(email)
        assert valid, f"Should be valid, got: {reason}"

    def test_missing_subject_fails(self):
        email = "Hi team, I want to apply."
        valid, reason = self._validate(email)
        assert not valid
        assert "SUBJECT" in reason

    def test_over_word_limit_fails(self):
        long_body = " ".join(["word"] * 250)
        email = f"SUBJECT: Test Role\n\n{long_body}"
        valid, reason = self._validate(email)
        assert not valid
        assert "long" in reason.lower()

    def test_banned_phrase_fails(self):
        email = "SUBJECT: Test\n\nI am writing to express my interest in this role."
        valid, reason = self._validate(email)
        assert not valid
        assert "banned" in reason.lower()

    def test_no_body_fails(self):
        email = "SUBJECT: Test only subject"
        valid, reason = self._validate(email)
        assert not valid


class TestEmailWriter:

    def test_returns_string(self, mock_groq_response, sample_company_research):
        mock_groq_response.return_value.content = (
            "SUBJECT: AI Engineer @ TestCo — Python expertise\n\n"
            "Hi, I noticed TestCo uses Python heavily. "
            "I built production APIs serving 10k req/s. Open to a 15-min call?"
        )
        from tools.email import email_writer
        result = email_writer.invoke({
            "company_name": "TestCo",
            "role": "AI Engineer",
            "company_research_summary": sample_company_research,
            "user_profile": "Python developer, 2 years experience",
            "tone": "professional"
        })
        assert isinstance(result, str)
        assert len(result) > 20

    def test_invalid_tone_defaults_to_professional(self, mock_groq_response, sample_company_research):
        mock_groq_response.return_value.content = (
            "SUBJECT: Test\n\nShort email body here. Let's talk for 15 minutes?"
        )
        from tools.email import email_writer
        result = email_writer.invoke({
            "company_name": "TestCo",
            "role": "Dev",
            "company_research_summary": sample_company_research,
            "user_profile": "Developer",
            "tone": "nonexistent_tone"  # invalid → should default to professional
        })
        assert isinstance(result, str)

    def test_handles_groq_error_gracefully(self, mocker, sample_company_research):
        mocker.patch("langchain_groq.ChatGroq.invoke", side_effect=Exception("API down"))
        from tools.email import email_writer
        result = email_writer.invoke({
            "company_name": "ErrorCo",
            "role": "Dev",
            "company_research_summary": sample_company_research,
            "user_profile": "Dev",
        })
        assert isinstance(result, str)
        assert "Error" in result
```

---

## FASE 4 — MARKET ANALYZER TOOL

**GitHub Issue:** #4
**Branch:** `feat/fase-4-market`

### Implementasi tools/market.py:

```python
"""
tools/market.py
Tool: market_analyzer
Analyze job market demand + skill gap for a given role
"""

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from tavily import TavilyClient
from config import GROQ_API_KEY, TAVILY_API_KEY, MODEL_FAST


def _get_llm():
    return ChatGroq(model=MODEL_FAST, api_key=GROQ_API_KEY, temperature=0.2)


@tool
def market_analyzer(
    target_role: str,
    user_skills: str,
    location: str = "Indonesia"
) -> str:
    """
    Analyze job market demand for a role and identify your skill gaps.
    Returns top demanded skills, what you're missing, learning priorities, salary range.

    Args:
        target_role: Role to analyze (e.g., "AI Engineer", "Backend Engineer")
        user_skills: Your current skills as comma-separated string
                     (e.g., "Python, FastAPI, LangChain, SQL")
        location: Job market location (default: "Indonesia")

    Returns:
        Structured market report with skill gap analysis and salary range
    """
    client = TavilyClient(api_key=TAVILY_API_KEY)
    llm = _get_llm()

    # Search job market data
    snippets = []
    queries = [
        f"{target_role} required skills {location} 2025",
        f"{target_role} job market demand salary {location}",
        f"{target_role} top companies hiring {location} 2025",
    ]

    for q in queries:
        try:
            resp = client.search(q, max_results=3, search_depth="basic")
            for r in resp.get("results", []):
                snippets.append(f"- {r.get('title','')}: {r.get('content','')[:300]}")
        except Exception:
            continue

    raw_data = "\n".join(snippets[:10]) if snippets else "No market data found."

    prompt = f"""Analyze the job market for: {target_role} in {location}

Market data from web:
{raw_data}

Applicant's current skills: {user_skills}

Produce a structured analysis in this EXACT format:

## Market Analysis: {target_role} ({location})

**Top 5 Skills Companies Want:**
1. [skill] [✓ if user has it, ✗ if missing]
2. [skill] [✓ or ✗]
3. [skill] [✓ or ✗]
4. [skill] [✓ or ✗]
5. [skill] [✓ or ✗]

**Your Match Score:** [X/5 skills (Y%)]

**Priority Skills to Learn Next:**
→ #1: [skill] — [why it matters + realistic time to learn basics]
→ #2: [skill] — [why it matters + realistic time to learn basics]

**Salary Range ({location}):**
- Junior (0-2yr): [range in IDR/month]
- Mid (2-4yr): [range in IDR/month]
- Senior (4yr+): [range in IDR/month]

**Top Companies Hiring Now:** [3-5 company names from search results]

Keep it factual. Only list skills that genuinely appear in job postings."""

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Market analysis unavailable. Error: {str(e)}"
```

### tests/test_market.py:

```python
"""tests/test_market.py"""

import pytest


class TestMarketAnalyzer:

    def test_returns_string(self, mock_tavily, mock_groq_response):
        mock_groq_response.return_value.content = "## Market Analysis: AI Engineer (Indonesia)\n\n**Top 5 Skills:**\n1. Python ✓"
        from tools.market import market_analyzer
        result = market_analyzer.invoke({
            "target_role": "AI Engineer",
            "user_skills": "Python, FastAPI"
        })
        assert isinstance(result, str)
        assert len(result) > 10

    def test_default_location_indonesia(self, mock_tavily, mock_groq_response):
        mock_groq_response.return_value.content = "Analysis here"
        from tools.market import market_analyzer
        # Should not raise even without location param
        result = market_analyzer.invoke({
            "target_role": "Backend Engineer",
            "user_skills": "Python"
        })
        assert isinstance(result, str)

    def test_handles_tavily_failure(self, mocker, mock_groq_response):
        mocker.patch("tavily.TavilyClient.search", side_effect=Exception("Network error"))
        mock_groq_response.return_value.content = "Analysis with no market data"
        from tools.market import market_analyzer
        result = market_analyzer.invoke({
            "target_role": "Dev",
            "user_skills": "Python"
        })
        assert isinstance(result, str)

    def test_handles_groq_failure(self, mock_tavily, mocker):
        mocker.patch("langchain_groq.ChatGroq.invoke", side_effect=Exception("LLM error"))
        from tools.market import market_analyzer
        result = market_analyzer.invoke({
            "target_role": "Dev",
            "user_skills": "Python"
        })
        assert "Error" in result
        assert isinstance(result, str)
```

---

## FASE 5 — LANGGRAPH AGENT CORE

**GitHub Issue:** #5
**Branch:** `feat/fase-5-agent`

### Implementasi agent.py (lengkap):

```python
"""
agent.py
JobHunterAI — LangGraph Agent Core
ReAct loop: agent node → tools node → agent node → ...
"""

import uuid
from typing import Annotated, TypedDict, Generator
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from tools.research import company_research
from tools.email import email_writer
from tools.tracker import track_application, check_followups, update_application_status
from tools.market import market_analyzer
from config import GROQ_API_KEY, MODEL_FAST, MAX_AGENT_ITERATIONS

# ─── Tools registry ──────────────────────────────────────────────────────────

ALL_TOOLS = [
    company_research,
    email_writer,
    track_application,
    check_followups,
    update_application_status,
    market_analyzer,
]

# ─── State ────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_profile: dict
    session_id: str
    iteration_count: int  # guard against infinite loop


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are JobHunterAI, an autonomous job search assistant for Indonesian tech professionals.

## Your Tools
- company_research: Research any company BEFORE applying. Always use this first.
- email_writer: Write personalized cold emails. Requires company research output.
- track_application: Save/update applications in database. Call after email is drafted.
- check_followups: Find applications needing follow-up (no reply after N days).
- update_application_status: Update status of existing application.
- market_analyzer: Analyze job market demand + skill gaps for a role.

## Behavior Rules
1. WORKFLOW for new application: company_research → email_writer → track_application
   Never skip company_research before email_writer. Ever.
2. After completing any task, suggest a concrete next action.
3. Show your tool usage transparently: "[Researching Tokopedia...]", "[Writing email...]"
4. Present final emails in code blocks for easy copy-paste.
5. When user asks about skills/market: use market_analyzer with their profile skills.
6. Be proactive: if user says "apply to X", do the full workflow without being asked step by step.

## Output Format
- Tool activity: [Tool name: brief description of what you're doing]
- Final email: Present inside ``` code block ```
- Always end with: "**Next step:** [specific suggestion]"

## User Profile
{user_profile}
"""

# ─── LLM ─────────────────────────────────────────────────────────────────────

def _get_llm():
    return ChatGroq(
        model=MODEL_FAST,
        api_key=GROQ_API_KEY,
        temperature=0.5
    ).bind_tools(ALL_TOOLS)


# ─── Nodes ────────────────────────────────────────────────────────────────────

def agent_node(state: AgentState) -> dict:
    messages = list(state["messages"])
    iteration = state.get("iteration_count", 0)

    # Guard: prevent infinite loop
    if iteration >= MAX_AGENT_ITERATIONS:
        return {
            "messages": [AIMessage(content="⚠️ Reached maximum iterations. Please try a simpler request.")],
            "iteration_count": iteration + 1
        }

    # Inject system prompt if not present
    if not any(isinstance(m, SystemMessage) for m in messages):
        profile_str = str(state.get("user_profile", {}))
        system = SystemMessage(
            content=SYSTEM_PROMPT.format(user_profile=profile_str)
        )
        messages = [system] + messages

    llm = _get_llm()
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "iteration_count": iteration + 1
    }


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


# ─── Graph ────────────────────────────────────────────────────────────────────

memory = MemorySaver()

_graph = StateGraph(AgentState)
_graph.add_node("agent", agent_node)
_graph.add_node("tools", ToolNode(ALL_TOOLS))

_graph.set_entry_point("agent")
_graph.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    END: END
})
_graph.add_edge("tools", "agent")

app = _graph.compile(checkpointer=memory)


# ─── Public Interface ─────────────────────────────────────────────────────────

def run_agent(
    user_message: str,
    user_profile: dict,
    session_id: str = None,
    history: list = None,
) -> tuple[list, str]:
    """
    Run the agent and return (updated_messages, final_response_text).

    Args:
        user_message: User's input
        user_profile: Dict with name, skills, experience, target_role
        session_id: For conversation memory (auto-generated if None)
        history: Previous messages for multi-turn conversation

    Returns:
        Tuple of (all_messages, last_response_text)
    """
    sid = session_id or str(uuid.uuid4())
    messages = list(history or [])
    messages.append(HumanMessage(content=user_message))

    config = {"configurable": {"thread_id": sid}}

    result = app.invoke({
        "messages": messages,
        "user_profile": user_profile,
        "session_id": sid,
        "iteration_count": 0,
    }, config=config)

    final_messages = result["messages"]
    last_ai = next(
        (m for m in reversed(final_messages) if isinstance(m, AIMessage)),
        None
    )
    final_text = last_ai.content if last_ai else ""

    return final_messages, final_text


def stream_agent(
    user_message: str,
    user_profile: dict,
    session_id: str = None,
) -> Generator[str, None, None]:
    """
    Stream agent responses token by token.
    Yields: partial text strings for Streamlit st.write_stream()
    """
    sid = session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": sid}}

    messages = [HumanMessage(content=user_message)]

    for chunk in app.stream({
        "messages": messages,
        "user_profile": user_profile,
        "session_id": sid,
        "iteration_count": 0,
    }, config=config, stream_mode="values"):
        last = chunk["messages"][-1]
        if isinstance(last, AIMessage) and last.content:
            yield last.content


def health_check() -> dict:
    return {
        "status": "ok",
        "tools_registered": len(ALL_TOOLS),
        "tool_names": [t.name for t in ALL_TOOLS],
        "model": MODEL_FAST,
    }


if __name__ == "__main__":
    profile = {
        "name": "Budi Santoso",
        "skills": ["Python", "FastAPI", "LangChain", "SQL"],
        "experience": "Semester 8 Informatika, 6 bulan internship fintech",
        "target_role": "AI Engineer"
    }

    print("JobHunterAI started. Type 'quit' to exit.\n")
    history = []
    session = str(uuid.uuid4())

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        messages, response = run_agent(user_input, profile, session, history)
        history = messages
        print(f"\nAgent: {response}\n")
```

### tests/test_agent.py (unit + integration):

```python
"""
tests/test_agent.py
Unit tests (no real API) + integration tests (needs real API keys)
Run unit tests: pytest tests/test_agent.py -v -m "not integration"
Run all: pytest tests/test_agent.py -v
"""

import pytest


class TestAgentUnit:
    """Unit tests — mock semua API calls."""

    def test_health_check(self):
        from agent import health_check
        result = health_check()
        assert result["status"] == "ok"
        assert result["tools_registered"] == 6
        assert "company_research" in result["tool_names"]

    def test_run_agent_returns_tuple(self, mocker):
        """Mock LLM to return simple response without tool calls."""
        from langchain_core.messages import AIMessage

        mock_response = AIMessage(content="Hello! How can I help you find a job?")
        mock_response.tool_calls = []
        mocker.patch("langchain_groq.ChatGroq.invoke", return_value=mock_response)

        from agent import run_agent
        messages, text = run_agent(
            user_message="Hello",
            user_profile={"name": "Test", "skills": [], "experience": "", "target_role": "Dev"},
            session_id="test-session-123"
        )
        assert isinstance(messages, list)
        assert isinstance(text, str)

    def test_all_tools_registered(self):
        from agent import ALL_TOOLS
        tool_names = [t.name for t in ALL_TOOLS]
        assert "company_research" in tool_names
        assert "email_writer" in tool_names
        assert "track_application" in tool_names
        assert "check_followups" in tool_names
        assert "update_application_status" in tool_names
        assert "market_analyzer" in tool_names

    def test_graph_compiled(self):
        from agent import app
        assert app is not None


@pytest.mark.integration
class TestAgentIntegration:
    """
    Integration tests — butuh real API keys.
    Skip otomatis jika GROQ_API_KEY = "test-groq-key" (CI mode)
    """

    @pytest.fixture(autouse=True)
    def skip_without_real_keys(self):
        import os
        if os.environ.get("GROQ_API_KEY", "").startswith("test-"):
            pytest.skip("Integration test skipped: no real API key")

    def test_simple_followup_check(self, temp_db):
        from agent import run_agent
        profile = {
            "name": "Test User",
            "skills": ["Python"],
            "experience": "Student",
            "target_role": "Dev"
        }
        messages, text = run_agent("Check if I have any applications needing follow-up", profile)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_market_analysis(self):
        from agent import run_agent
        profile = {
            "name": "Test",
            "skills": ["Python", "FastAPI"],
            "experience": "Student",
            "target_role": "AI Engineer"
        }
        messages, text = run_agent(
            "Analyze the AI Engineer job market for my skills: Python, FastAPI",
            profile
        )
        assert isinstance(text, str)
        assert len(text) > 50
```

---

## FASE 6 — STREAMLIT UI

**GitHub Issue:** #6
**Branch:** `feat/fase-6-ui`

### Implementasi ui/app.py (lengkap):

```python
"""
ui/app.py
JobHunterAI — Streamlit Chat Interface
Features: multi-turn chat, streaming, application tracker, stats, CSV export
Run: streamlit run ui/app.py
"""

import streamlit as st
import uuid
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import run_agent
from tools.tracker import get_all_applications, get_stats, delete_application, export_to_csv, update_application_status
from config import VALID_STATUSES, GROQ_API_KEY, TAVILY_API_KEY
from langchain_core.messages import HumanMessage, AIMessage

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="JobHunterAI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Session State Init ───────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "quick_cmd" not in st.session_state:
    st.session_state.quick_cmd = None

# ─── API Key Check ────────────────────────────────────────────────────────────

def check_api_keys():
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    return missing

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🎯 JobHunterAI")
    st.caption("AI Agent for job applications")

    # API Key warning
    missing_keys = check_api_keys()
    if missing_keys:
        st.error(f"Missing API keys: {', '.join(missing_keys)}\n\nAdd them to your `.env` file.")
        st.markdown("- Groq: [console.groq.com](https://console.groq.com)")
        st.markdown("- Tavily: [tavily.com](https://tavily.com)")
        st.stop()

    st.divider()

    # User Profile
    st.subheader("Your Profile")
    name = st.text_input("Name", value=st.session_state.get("profile_name", ""), placeholder="Your full name")
    target_role = st.text_input("Target Role", value=st.session_state.get("profile_role", ""), placeholder="AI Engineer")
    experience = st.text_area(
        "Experience",
        value=st.session_state.get("profile_exp", ""),
        height=80,
        placeholder="e.g., Semester 8 CS, 6-month fintech internship"
    )
    skills = st.text_input(
        "Skills (comma-separated)",
        value=st.session_state.get("profile_skills", ""),
        placeholder="Python, FastAPI, LangChain, SQL"
    )

    # Save profile to session
    if name:
        st.session_state.profile_name = name
        st.session_state.profile_role = target_role
        st.session_state.profile_exp = experience
        st.session_state.profile_skills = skills

    user_profile = {
        "name": name or "User",
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
        "experience": experience or "",
        "target_role": target_role or "Software Engineer"
    }

    st.divider()

    # Stats
    st.subheader("📊 Application Stats")
    stats = get_stats()
    col1, col2 = st.columns(2)
    col1.metric("Total", stats["total"])
    col2.metric("Interviews", stats["by_status"].get("interview_scheduled", 0))
    col3, col4 = st.columns(2)
    col3.metric("Sent", stats["by_status"].get("sent", 0))
    col4.metric("Offers", stats["by_status"].get("offer_received", 0))

    st.divider()

    # Quick Actions
    st.subheader("⚡ Quick Actions")
    if st.button("📋 Check Follow-ups", use_container_width=True):
        st.session_state.quick_cmd = "Check which of my job applications need a follow-up email"
    if st.button("📊 Market Analysis", use_container_width=True):
        skill_str = skills or "Python"
        st.session_state.quick_cmd = f"Analyze the job market for {target_role or 'Software Engineer'} with my skills: {skill_str}"
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# ─── Main Area ────────────────────────────────────────────────────────────────

st.title("🎯 JobHunterAI")
st.caption("Tell me a company to research, or ask me to check your follow-ups.")

# Application Tracker expander
with st.expander("📁 Application Tracker", expanded=False):
    apps = get_all_applications()
    if not apps:
        st.info("No applications tracked yet. Ask the agent to apply to a company!")
    else:
        # Export CSV button
        csv_data = export_to_csv()
        if csv_data:
            st.download_button(
                "⬇️ Export CSV",
                data=csv_data,
                file_name="job_applications.csv",
                mime="text/csv"
            )

        # Application table
        STATUS_EMOJI = {
            "email_drafted": "🟡", "sent": "🔵", "replied": "🟢",
            "interview_scheduled": "🟣", "interview_done": "🟤",
            "offer_received": "⭐", "rejected": "🔴", "withdrawn": "⚪"
        }

        for app in apps:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                col1.write(f"**{app['company']}** — {app['role']}")
                emoji = STATUS_EMOJI.get(app["status"], "⚪")
                
                # Status dropdown
                new_status = col2.selectbox(
                    "Status",
                    options=VALID_STATUSES,
                    index=VALID_STATUSES.index(app["status"]) if app["status"] in VALID_STATUSES else 0,
                    key=f"status_{app['id']}",
                    label_visibility="collapsed"
                )
                if new_status != app["status"]:
                    update_application_status.invoke({
                        "company": app["company"],
                        "role": app["role"],
                        "new_status": new_status
                    })
                    st.rerun()

                col3.write(app.get("applied_at", "")[:10])
                
                # View email draft
                if app.get("email_draft") and col4.button("📧 View", key=f"view_{app['id']}"):
                    st.code(app["email_draft"], language="text")
                
                # Delete button
                if col5.button("🗑", key=f"del_{app['id']}"):
                    delete_application(app["id"])
                    st.rerun()

                st.divider()

# ─── Chat Messages ────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content if isinstance(msg.content, str) else str(msg.content))
    elif isinstance(msg, AIMessage):
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if content:  # Skip empty AI messages (tool calls)
            with st.chat_message("assistant"):
                st.markdown(content)

# ─── Chat Input ───────────────────────────────────────────────────────────────

user_input = st.session_state.quick_cmd or st.chat_input(
    "e.g., 'Research Tokopedia and apply for AI Engineer role'"
)
st.session_state.quick_cmd = None  # reset after use

if user_input:
    if not name:
        st.warning("Please enter your name in the sidebar first.")
        st.stop()

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Agent working..."):
            try:
                updated_messages, final_text = run_agent(
                    user_message=user_input,
                    user_profile=user_profile,
                    session_id=st.session_state.session_id,
                    history=st.session_state.messages.copy()
                )
                st.session_state.messages = updated_messages
                st.markdown(final_text)
            except Exception as e:
                error_msg = f"⚠️ Agent error: {str(e)}\n\nTry again or simplify your request."
                st.error(error_msg)

    st.rerun()  # refresh stats di sidebar
```

**.streamlit/config.toml:**
```toml
[theme]
primaryColor = "#7F77DD"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#1A1A1A"
font = "sans serif"

[server]
maxUploadSize = 10
headless = true
```

---

## FASE 7 — DEPLOY KE RAILWAY

**GitHub Issue:** #7
**Branch:** `feat/fase-7-deploy`

### Procfile:
```
web: streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### railway.json:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true",
    "healthcheckPath": "/",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### Dockerfile (untuk local testing):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "ui/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

### Pre-deploy checklist (jalankan ini):
```bash
# 1. Pastikan semua unit test pass
pytest tests/ -v -m "not integration" --tb=short

# 2. Lint
ruff check . --fix
black .

# 3. Cek requirements up to date
pip freeze | grep -E "(langgraph|langchain|tavily|streamlit)" > /dev/null && echo "OK"

# 4. Test Docker build lokal
docker build -t jobhunterai:latest .
docker run --env-file .env -p 8501:8501 jobhunterai:latest

# 5. Buka browser → localhost:8501 → test manual:
#    - Isi nama di sidebar
#    - Ketik: "Check follow-ups"
#    - Pastikan response muncul tanpa error

# 6. Push final
git add .
git commit -m "feat: add deploy config (Procfile, Dockerfile, railway.json)"
git push origin feat/fase-7-deploy
```

### Deploy ke Railway:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Init project (pilih "Empty Project")
railway init

# Deploy
railway up

# Set environment variables
railway variables set GROQ_API_KEY=gsk_...
railway variables set TAVILY_API_KEY=tvly-...
railway variables set GOOGLE_API_KEY=AIza...

# Buka URL
railway open
```

---

## 🔁 FULL TEST SUITE — JALANKAN SEBELUM SETIAP PUSH

```bash
# Unit tests only (tidak butuh API key)
pytest tests/ -v -m "not integration" --tb=short --cov=tools --cov-report=term-missing

# Semua test (butuh real API keys, untuk integration test)
pytest tests/ -v --tb=short

# Quick smoke test
python -c "from agent import health_check; print(health_check())"

# Lint
ruff check . && black --check .
```

---

## 📋 GITHUB WORKFLOW SUMMARY

Setiap push ke repo ini:
1. **GitHub Actions CI** jalan otomatis (lihat `.github/workflows/ci.yml`)
2. Unit tests dijalankan tanpa API key
3. Lint check (ruff)
4. Badge CI di README update otomatis

Jika CI gagal:
```bash
# Lihat log di GitHub → Actions tab
# Fix locally → push lagi
git add . && git commit -m "fix: [apa yang difix]" && git push
```

Jika perlu rollback:
```bash
# Lihat history commit
git log --oneline -10

# Rollback ke commit tertentu
git revert HEAD        # undo commit terakhir (buat commit baru)
git revert abc123      # undo commit spesifik

# ATAU hard reset (hati-hati, destructive)
git reset --hard abc123
git push --force-with-lease
```

---

## ✅ DEFINITION OF DONE (PER FASE)

Fase dianggap SELESAI jika semua ini terpenuhi:

- [ ] Semua fungsi terimplementasi sesuai spec di atas
- [ ] `pytest tests/test_NAMA.py -v` → semua PASS, 0 FAILED
- [ ] `ruff check .` → 0 error
- [ ] Code ter-push ke branch `feat/fase-N-nama`
- [ ] PR dibuat dan di-merge ke `main`
- [ ] GitHub Issue #N di-close dengan komentar "All tests passing ✓"
- [ ] `git pull` di main → jalankan full test suite → masih semua PASS

Tidak ada fase yang skip. Tidak ada "nanti di-test-nya". Test dulu, baru lanjut.
Done

You are out of free m