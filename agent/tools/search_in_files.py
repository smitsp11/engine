"""
Fake search tool.

This simulates searching over files. It returns a deterministic mock list
of "matches" based on the query text length, so that tests remain stable.
"""

from __future__ import annotations

from typing import Any, Dict, List


def search_in_files(payload: Dict[str, Any]) -> Dict[str, Any]:
    query = str(payload.get("query", "")).strip()

    if not query:
        # Explicit "no results" when there is no query.
        return {"results": []}

    # Deterministic pseudo-results: number of mock hits is a simple function
    # of the query length, capped at 3.
    count = min(len(query) // 10 + 1, 3)
    results: List[Dict[str, Any]] = [
        {
            "file": f"mock_file_{i}.txt",
            "line": i * 10 + 1,
            "snippet": f"Mock match {i} for query: {query}",
        }
        for i in range(1, count + 1)
    ]
    return {"results": results}


__all__ = ["search_in_files"]


