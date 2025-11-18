"""
Snapshot system for regression testing.

Compares current outputs against previously saved "golden" outputs.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class Snapshot:
    """Manages snapshot comparisons for regression testing."""

    def __init__(self, snapshot_dir: str = "tests/snapshots"):
        """
        Initialize snapshot system.
        
        Parameters
        ----------
        snapshot_dir: str
            Directory to store snapshots
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def get_snapshot_path(self, test_id: str) -> Path:
        """Get the path to a snapshot file."""
        return self.snapshot_dir / f"{test_id}.snapshot.json"

    def save(self, test_id: str, output: Dict[str, Any]) -> None:
        """
        Save a snapshot of the output.
        
        Parameters
        ----------
        test_id: str
            Test identifier
        output: Dict[str, Any]
            Output to save
        """
        snapshot_path = self.get_snapshot_path(test_id)
        with open(snapshot_path, "w") as f:
            json.dump(output, f, indent=2, sort_keys=True)

    def load(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved snapshot.
        
        Parameters
        ----------
        test_id: str
            Test identifier
        
        Returns
        -------
        Optional[Dict[str, Any]]
            Snapshot data or None if not found
        """
        snapshot_path = self.get_snapshot_path(test_id)
        if not snapshot_path.exists():
            return None
        
        with open(snapshot_path, "r") as f:
            return json.load(f)

    def compare(
        self, 
        test_id: str, 
        new_output: Dict[str, Any],
        update: bool = False
    ) -> List[str]:
        """
        Compare new output against saved snapshot.
        
        Parameters
        ----------
        test_id: str
            Test identifier
        new_output: Dict[str, Any]
            New output to compare
        update: bool
            If True, update snapshot if differences found
        
        Returns
        -------
        List[str]
            List of differences found (empty if identical)
        """
        old_output = self.load(test_id)
        
        if old_output is None:
            # No snapshot exists, create one
            self.save(test_id, new_output)
            return []

        differences = []

        # Compare structure
        old_keys = set(self._flatten_dict(old_output).keys())
        new_keys = set(self._flatten_dict(new_output).keys())

        missing_keys = old_keys - new_keys
        added_keys = new_keys - old_keys

        if missing_keys:
            differences.append(f"Missing keys: {', '.join(sorted(missing_keys)[:5])}")
        if added_keys:
            differences.append(f"Added keys: {', '.join(sorted(added_keys)[:5])}")

        # Compare critical fields
        critical_fields = ["status", "plan", "steps"]
        for field in critical_fields:
            if field in old_output and field in new_output:
                if old_output[field] != new_output[field]:
                    differences.append(f"Field '{field}' changed")

        # Compare plan structure
        if "plan" in old_output and "plan" in new_output:
            old_plan = old_output["plan"]
            new_plan = new_output["plan"]
            
            if len(old_plan) != len(new_plan):
                differences.append(
                    f"Plan length changed: {len(old_plan)} -> {len(new_plan)}"
                )
            else:
                # Compare step IDs
                old_ids = {step.get("id") for step in old_plan}
                new_ids = {step.get("id") for step in new_plan}
                if old_ids != new_ids:
                    differences.append("Plan step IDs changed")

        # Update snapshot if requested and differences found
        if update and differences:
            self.save(test_id, new_output)

        return differences

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """Flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(
                            self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items()
                        )
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
        return dict(items)


__all__ = ["Snapshot"]

