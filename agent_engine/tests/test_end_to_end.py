from agent_engine import run_agent


def test_run_agent_does_not_crash_and_returns_summary():
    summary = run_agent("Plan a birthday party")

    assert isinstance(summary, dict)
    assert summary["task"] == "Plan a birthday party"
    assert summary["status"] in {"succeeded", "partial_success", "failed"}

    # Plan and results should be present and list-like.
    assert isinstance(summary.get("plan"), list)
    assert len(summary["plan"]) >= 1
    assert isinstance(summary.get("results"), list)


