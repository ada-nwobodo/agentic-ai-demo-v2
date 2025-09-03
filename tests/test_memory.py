from agent.memory import summarize_history_for_context

def test_summary_basic():
    history = [
        {"role": "user", "content": "I need help with hypertension management.", "created_at": 1},
        {"role": "assistant", "content": "Sure, let's start with your latest readings.", "created_at": 2},
        {"role": "user", "content": "Average BP 152/94, age 55, on amlodipine.", "created_at": 3},
        {"role": "assistant", "content": "Thanks. We should check guidelines and consider therapy escalation.", "created_at": 4},
    ]
    out = summarize_history_for_context(history, max_chars=300)
    assert "Initial user intent" in out
    assert "Latest assistant advice" in out
    assert "Recent exchanges" in out
