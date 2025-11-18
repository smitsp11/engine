#!/usr/bin/env python3
"""
Master test runner for Agent Engine evaluation framework.

Runs all tests, validates results, and generates reports.
"""

import os
import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from test_runner import AgentTestRunner
from evaluator import Evaluator
from snapshot import Snapshot
from scoring import Scoring


class TestSuite:
    """Manages and runs the complete test suite."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize test suite."""
        self.runner = AgentTestRunner(base_url=base_url)
        self.evaluator = Evaluator()
        self.snapshot = Snapshot()
        self.scoring = Scoring()
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def find_tests(self) -> List[Path]:
        """Find all test JSON files."""
        test_files = []
        test_dirs = [
            "tests/planning",
            "tests/tool_selection",
            "tests/execution",
            "tests/end_to_end",
            "tests/stress",
            "tests/regression",
        ]
        
        for test_dir in test_dirs:
            dir_path = Path(test_dir)
            if dir_path.exists():
                for test_file in dir_path.glob("*.json"):
                    if "template" not in test_file.name and "snapshot" not in test_file.name:
                        test_files.append(test_file)
        
        return sorted(test_files)

    def run_test(self, test_file: Path) -> Dict[str, Any]:
        """
        Run a single test and return results.
        
        Parameters
        ----------
        test_file: Path
            Path to test JSON file
        
        Returns
        -------
        Dict[str, Any]
            Test result with validation and scoring
        """
        with open(test_file) as f:
            test = json.load(f)

        test_id = test.get("id", test_file.stem)
        category = test.get("category", "unknown")
        expected = test.get("expected", {})

        print(f"\n{'='*60}")
        print(f"Running: {test_id} ({category})")
        print(f"{'='*60}")

        # Run the test
        execution_result = self.runner.run_test(test)
        
        if execution_result["status"] != "success":
            return {
                "test_id": test_id,
                "category": category,
                "status": "ERROR",
                "error": execution_result.get("error"),
                "score": 0.0,
                "passed": False,
            }

        result = execution_result["result"]

        # Validate plan
        plan = result.get("plan", [])
        plan_errors = self.evaluator.validate_plan(plan, expected)

        # Validate tool selection (if category requires it)
        tool_errors = []
        if category in ["tool_selection", "planning"]:
            tool_errors = self.evaluator.validate_tool_selection(plan, expected)

        # Validate execution (if category requires it)
        exec_errors = []
        if category in ["execution", "end_to_end"]:
            exec_errors = self.evaluator.validate_execution(result, expected)

        # Compare snapshot
        snapshot_diffs = self.snapshot.compare(test_id, result, update=False)

        # Score output
        criteria = expected.get("criteria", {})
        output_scores = {}
        if criteria:
            output_scores = self.evaluator.score_output(result, criteria)

        # Calculate overall score
        all_errors = plan_errors + tool_errors + exec_errors
        score = self.scoring.calculate_test_score(
            execution_result,
            all_errors,
            snapshot_diffs,
            output_scores
        )

        # Print results
        if all_errors:
            print(f"  ❌ Validation Errors ({len(all_errors)}):")
            for error in all_errors[:5]:  # Show first 5
                print(f"    - {error}")
        
        if snapshot_diffs:
            print(f"  ⚠️  Snapshot Differences ({len(snapshot_diffs)}):")
            for diff in snapshot_diffs[:3]:  # Show first 3
                print(f"    - {diff}")
        
        print(f"  📊 Score: {score['total_score']}/100")
        print(f"  {'✅ PASS' if score['passed'] else '❌ FAIL'}")

        return {
            "test_id": test_id,
            "category": category,
            "status": "PASS" if score["passed"] else "FAIL",
            "score": score["total_score"],
            "passed": score["passed"],
            "execution_time": execution_result.get("execution_time", 0),
            "plan_errors": plan_errors,
            "tool_errors": tool_errors,
            "exec_errors": exec_errors,
            "snapshot_diffs": snapshot_diffs,
            "output_scores": output_scores,
            "error": None,
        }

    def run_all(self, update_snapshots: bool = False) -> Dict[str, Any]:
        """
        Run all tests in the suite.
        
        Parameters
        ----------
        update_snapshots: bool
            If True, update snapshots when differences found
        
        Returns
        -------
        Dict[str, Any]
            Summary of all test results
        """
        # Check API health
        if not self.runner.health_check():
            print("❌ API server is not running!")
            print("   Start it with: uvicorn api.app:app --reload")
            sys.exit(1)

        test_files = self.find_tests()
        
        if not test_files:
            print("⚠️  No test files found!")
            return {"total": 0, "passed": 0, "failed": 0}

        print(f"\n🧪 Found {len(test_files)} test(s)")
        print(f"{'='*60}\n")

        results = []
        for test_file in test_files:
            result = self.run_test(test_file)
            results.append(result)

        # Generate summary
        total = len(results)
        passed = sum(1 for r in results if r.get("passed", False))
        failed = total - passed
        avg_score = sum(r.get("score", 0) for r in results) / total if total > 0 else 0

        # Save results to CSV
        self.save_results_csv(results)

        # Print summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Average Score: {avg_score:.2f}/100")
        print(f"{'='*60}\n")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "avg_score": avg_score,
            "results": results,
        }

    def save_results_csv(self, results: List[Dict[str, Any]]) -> None:
        """Save test results to CSV file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.results_dir / f"results_{timestamp}.csv"

        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "test_id",
                "category",
                "status",
                "score",
                "execution_time",
                "plan_errors",
                "tool_errors",
                "exec_errors",
                "snapshot_diffs",
            ])
            
            for result in results:
                writer.writerow([
                    result.get("test_id", ""),
                    result.get("category", ""),
                    result.get("status", ""),
                    result.get("score", 0),
                    result.get("execution_time", 0),
                    len(result.get("plan_errors", [])),
                    len(result.get("tool_errors", [])),
                    len(result.get("exec_errors", [])),
                    len(result.get("snapshot_diffs", [])),
                ])

        print(f"💾 Results saved to: {csv_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Agent Engine test suite")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--update-snapshots",
        action="store_true",
        help="Update snapshots when differences found"
    )
    
    args = parser.parse_args()
    
    suite = TestSuite(base_url=args.url)
    summary = suite.run_all(update_snapshots=args.update_snapshots)
    
    # Exit with error code if tests failed
    if summary["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

