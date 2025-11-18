from agent_engine.agent.executor import Executor
from agent_engine.agent.memory import Memory
from agent_engine.agent.state import TaskState
from agent_engine.agent.schemas import Subtask, ToolName, SubtaskStatus


def make_simple_context():
    memory = Memory()
    state = TaskState()
    state.start_task("Simple test task")
    return memory, state


def test_executor_runs_generate_text_and_updates_state():
    memory, state = make_simple_context()
    executor = Executor(memory=memory, state=state)

    subtask = Subtask(
        id="step-1",
        description="Generate a greeting",
        tool=ToolName.GENERATE_TEXT,
        dependencies=[],
        success_criteria="Text should be generated.",
        deliverable="Greeting text.",
    )

    state.set_plan(type("P", (), {"subtasks": [subtask]})())  # minimal fake plan with .subtasks

    result = executor.execute_subtask(subtask)

    assert result.subtask_id == "step-1"
    assert result.status in (SubtaskStatus.SUCCEEDED, SubtaskStatus.FAILED)

    # Memory should have recorded an output for this subtask.
    assert "step-1" in memory.tool_outputs

    # State should have at least one subtask result recorded.
    assert len(state.subtask_results) == 1


