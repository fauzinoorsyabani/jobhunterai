# 🎯 JobHunterAI

AI Agent berbasis LangGraph untuk riset perusahaan target, cold email, dan job application tracking.

## Stack

- **LLM:** Groq (Llama 3.3 70B) — GRATIS
- **Search:** Tavily API — GRATIS 1000 req/bulan
- **Agent:** LangGraph 0.2+ (ReAct loop)
- **Database:** SQLite (lokal, no setup)
- **UI:** Streamlit
- **CI/CD:** GitHub Actions
- **Deploy:** Railway

## Quick Start

```bash
# 1. Clone
git clone https://github.com/USERNAME/jobhunterai.git
cd jobhunterai

# 2. Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# 3. Environment
cp .env.example .env
# Edit .env → tambahkan API keys

# 4. Run
streamlit run ui/app.py
```

## API Keys (Semua GRATIS)

| Key | Dapatkan di | Fungsi |
|-----|------------|--------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | LLM (email, research, market) |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Fallback LLM |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | Web search |

## Architecture

```
User Input → LangGraph Agent → Tools:
  ├── company_research (Tavily + Groq)
  ├── email_writer (Groq)
  ├── track_application (SQLite)
  ├── check_followups (SQLite)
  ├── update_application_status (SQLite)
  └── market_analyzer (Tavily + Groq)
```

## Testing

```bash
# Unit tests (no API key needed)
pytest tests/ -v -m "not integration" --tb=short

# All tests (needs real API keys)
pytest tests/ -v --tb=short
```
