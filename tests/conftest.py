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
