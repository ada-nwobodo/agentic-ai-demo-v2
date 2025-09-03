from typing import List, Dict, Tuple
import textwrap
import datetime

SYSTEM_CORE = """You are an agentic assistant in a Streamlit demo.
You must:
- Be context-aware: reference earlier user inputs and assistant responses
- Cite external guideline snippets that were provided in your context
- Be concise but actionable
- If information is uncertain, say so and suggest how to verify it
- Never fabricate URLs or guideline names that were not given
"""

def build_rich_prompt(user_input: str, context_summary: str, guidelines: List[Dict], meta: Dict) -> Tuple[str, str]:
    # Format guidelines into compact references included in the prompt
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    gl_lines = []
    for i, g in enumerate(guidelines[:10], start=1):
        title = g.get("title", "Untitled")
        summary = g.get("summary", "")
        url = g.get("url", "")
        source = g.get("source", "unknown")
        published = g.get("published_at", "unknown")
        gl_lines.append(f"[G{i}] {title} — {source} ({published})\n{summary}\n{url}")

    guideline_block = "\n\n".join(gl_lines) if gl_lines else "No external guidelines available."

    meta_bits = []
    if meta.get("user_name"):
        meta_bits.append(f"User name: {meta['user_name']}")
    if meta.get("domain"):
        meta_bits.append(f"Domain: {meta['domain']}")
    if meta.get("goal"):
        meta_bits.append(f"Goal: {meta['goal']}")
    meta_block = "\n".join(meta_bits) if meta_bits else "(no case metadata provided)"

    system_prompt = SYSTEM_CORE

    user_prompt = textwrap.dedent(f"""
    Timestamp: {now}

    Case metadata:
    {meta_block}

    Context summary from earlier messages:
    {context_summary}

    External guidelines and references (read-only context):
    {guideline_block}

    Task:
    1) Respond to the user's latest message below.
    2) Reference any relevant [G#] entries in your reasoning (e.g., "Per [G2] ...").
    3) Tailor your response to the user's prior inputs in this case.
    4) Provide next steps and, if relevant, questions to clarify.

    Latest user message:
    \"\"\"
    {user_input}
    \"\"\"
    """).strip()

    return system_prompt, user_prompt
