import os
import uuid
import time
import streamlit as st

from agent.storage import init_db, get_or_create_case, list_cases, save_message, get_history, set_case_meta, get_case_meta
from agent.memory import summarize_history_for_context
from agent.external_guidelines import GuidelinesClient, DemoGuidelinesClient
from agent.prompts import build_rich_prompt
from agent.llm import LLM, LLMConfig

st.set_page_config(page_title="Agentic AI Demo v2", page_icon="🤖", layout="wide")

# ---------------- Sidebar Controls ----------------
with st.sidebar:
    st.title("⚙️ Settings")
    default_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    api_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
    model = st.text_input("Model", value=default_model, help="Any chat-completions compatible model via the OpenAI Python SDK.")
    guidelines_base_url = st.text_input("Guidelines API Base URL (optional)",
                                        value=os.getenv("GUIDELINES_BASE_URL", ""),
                                        help="A REST endpoint responding to GET ?q=<query> with JSON items [{title, summary, url, source, published_at}].")
    max_guideline_results = st.number_input("Max guideline results", min_value=1, max_value=20, value=5, step=1)
    st.caption("Tip: Leave the base URL empty to use the built-in demo dataset so you can test without any external API.")

    st.markdown("---")
    st.caption("💾 Persistent storage: local SQLite 'agent.db'.")

# ---------------- Init Services ----------------
init_db(os.path.join(os.path.dirname(__file__), "agent.db"))

llm = LLM(LLMConfig(api_key=api_key, model=model))
guidelines_client = GuidelinesClient(base_url=guidelines_base_url) if guidelines_base_url else DemoGuidelinesClient()

# ---------------- Case Management ----------------
st.title("Agentic AI Demo v2 — Context-aware + Real-world Data")
col_new, col_select, col_refresh = st.columns([1,3,1])

with col_new:
    if st.button("🆕 New case"):
        case_id = str(uuid.uuid4())[:8]
        get_or_create_case(case_id)
        st.session_state["case_id"] = case_id
        st.success(f"Created new case: {case_id}")

with col_select:
    existing = list_cases(limit=200)
    selected = st.selectbox("Open an existing case", options=["— select —"] + [c["id"] for c in existing])
    if selected and selected != "— select —":
        st.session_state["case_id"] = selected

with col_refresh:
    if st.button("🔄 Refresh cases"):
        st.rerun()

case_id = st.session_state.get("case_id")
if not case_id:
    st.info("Create or select a case to begin.")
    st.stop()

st.subheader(f"Case: `{case_id}`")

# Case meta (e.g., user name, domain, goal)
with st.expander("Case details / metadata", expanded=False):
    meta = get_case_meta(case_id) or {}
    user_name = st.text_input("End-user name (optional)", value=meta.get("user_name", ""))
    domain = st.text_input("Domain/Topic (e.g., clinical triage, housing advice)", value=meta.get("domain", ""))
    goal = st.text_area("Primary goal for this case", value=meta.get("goal", ""))
    if st.button("Save case details"):
        set_case_meta(case_id, {"user_name": user_name, "domain": domain, "goal": goal})
        st.success("Saved case details.")

# ---------------- Conversation UI ----------------
history = get_history(case_id, limit=200)

with st.container(border=True):
    st.markdown("#### Conversation")
    for m in history:
        if m["role"] == "user":
            st.chat_message("user").markdown(m["content"])
        else:
            st.chat_message("assistant").markdown(m["content"])

user_input = st.chat_input("Type your next message, question, or case update...")
if user_input:
    save_message(case_id, "user", user_input)

    # Build context from prior history
    history = get_history(case_id, limit=200)
    context_summary = summarize_history_for_context(history, max_chars=1200)

    # Query guidelines client using a lightweight query (last user message + topic)
    query_hints = []
    meta = get_case_meta(case_id) or {}
    if meta.get("domain"):
        query_hints.append(meta["domain"])
    query_hints.append(user_input)
    query = " | ".join([q for q in query_hints if q])

    with st.spinner("Fetching external guidelines…"):
        try:
            guidelines = guidelines_client.search(query, max_results=max_guideline_results)
        except Exception as e:
            guidelines = []
            st.warning(f"Guidelines lookup failed: {e}")

    with st.expander("External guideline results", expanded=True):
        if not guidelines:
            st.write("No guidelines found for this query.")
        for g in guidelines:
            st.markdown(f"**{g.get('title','Untitled')}**  \n"
                        f"{g.get('summary','(no summary)')}  \n"
                        f"Source: {g.get('source','unknown')}  \n"
                        f"[Open link]({g.get('url','#')})  \n"
                        f"Published: {g.get('published_at','unknown')}")

    # Compose a rich prompt that references earlier inputs + real-world data
    system_prompt, user_prompt = build_rich_prompt(
        user_input=user_input,
        context_summary=context_summary,
        guidelines=guidelines,
        meta=meta
    )

    with st.spinner("Thinking…"):
        assistant_reply = llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)

    save_message(case_id, "assistant", assistant_reply)

    st.chat_message("assistant").markdown(assistant_reply)
    st.toast("Reply added to the case history.")


st.markdown("---")
with st.expander("🔎 How this works (technical)", expanded=False):
    st.markdown(
        """
        - **Context-aware prompts**: conversation history is summarized into a compact memory window.
        - **Richer prompts**: we stitch together prior user inputs, case metadata, and external guideline snippets.
        - **External APIs**: the `GuidelinesClient` performs REST lookups; a demo dataset is used if you don't set a base URL.
        - **Persistence**: all messages & metadata are stored in a local SQLite database (`agent.db`) so you can close the app and continue later.
        """
    )
