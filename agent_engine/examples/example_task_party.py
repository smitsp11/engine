"""
Example: plan a birthday party using the agent engine.
"""

from __future__ import annotations

from agent_engine import run_agent
from agent_engine.agent import utils


def main() -> None:
    task = "Plan a birthday party for my friend"
    utils.logger().info("Running example task", extra={"task": task})
    summary = run_agent(task)
    print(utils.to_json(summary, indent=2))


if __name__ == "__main__":
    main()


