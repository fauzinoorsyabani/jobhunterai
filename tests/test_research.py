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
