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
