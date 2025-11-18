from agent_engine.agent.planner import Planner
from agent_engine.agent.schemas import ToolName


def test_planner_produces_valid_plan_for_study_task():
    planner = Planner()
    plan = planner.create_plan("Plan my study schedule")

    # Basic shape
    assert plan.task == "Plan my study schedule"
    assert 5 <= len(plan.subtasks) <= 15

    # IDs are unique
    ids = [s.id for s in plan.subtasks]
    assert len(ids) == len(set(ids))

    # Dependencies refer to known IDs
    known_ids = set(ids)
    for s in plan.subtasks:
        for dep in s.dependencies:
            assert dep in known_ids

    # Study / research tasks should use SEARCH_IN_FILES and SAVE_OUTPUT at least once
    tools = {s.tool for s in plan.subtasks}
    assert ToolName.SEARCH_IN_FILES in tools
    assert ToolName.SAVE_OUTPUT in tools


