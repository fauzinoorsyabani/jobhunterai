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
