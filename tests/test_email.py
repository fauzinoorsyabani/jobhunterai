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
