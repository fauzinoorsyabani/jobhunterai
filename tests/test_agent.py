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
