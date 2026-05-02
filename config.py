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
