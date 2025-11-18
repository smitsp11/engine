"""
Example: research a topic using the agent.
"""

from __future__ import annotations

from agent.core import run_agent
from agent import utils


def main() -> None:
    task = "Research how solar panels work"
    utils.logger().info("Running example task", extra={"task": task})
    summary = run_agent(task)
    print(utils.to_json(summary, indent=2))


if __name__ == "__main__":
    main()



