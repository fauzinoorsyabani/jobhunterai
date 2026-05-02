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
