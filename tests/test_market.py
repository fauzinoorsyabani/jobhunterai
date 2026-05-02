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
