"""
Scoring system for test results.

Provides quantitative metrics for test quality.
"""

from typing import Dict, Any, List
from datetime import datetime


class Scoring:
    """Calculates and tracks scores for test results."""

    @staticmethod
    def calculate_test_score(
        test_result: Dict[str, Any],
        evaluator_errors: List[str],
        snapshot_differences: List[str],
        output_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate overall test score.
        
        Parameters
        ----------
        test_result: Dict[str, Any]
            Test execution result
        evaluator_errors: List[str]
            Validation errors
        snapshot_differences: List[str]
            Snapshot differences
        output_scores: Dict[str, float]
            Output quality scores
        
        Returns
        -------
        Dict[str, Any]
            Complete score breakdown
        """
        base_score = 100.0

        # Deduct for validation errors
        error_penalty = len(evaluator_errors) * 10
        base_score -= error_penalty

        # Deduct for snapshot differences
        diff_penalty = len(snapshot_differences) * 5
        base_score -= diff_penalty

        # Deduct for execution failures
        if test_result.get("status") != "success":
            base_score -= 30

        # Add bonus for output quality
        quality_bonus = 0
        if output_scores:
            avg_quality = sum(output_scores.values()) / len(output_scores)
            quality_bonus = (avg_quality / 5.0) * 10  # Up to 10 points

        final_score = max(0, min(100, base_score + quality_bonus))

        return {
            "total_score": round(final_score, 2),
            "base_score": 100.0,
            "error_penalty": error_penalty,
            "diff_penalty": diff_penalty,
            "quality_bonus": round(quality_bonus, 2),
            "output_scores": output_scores,
            "passed": final_score >= 70.0,  # 70% threshold
        }

    @staticmethod
    def format_score_report(score: Dict[str, Any]) -> str:
        """
        Format score as human-readable report.
        
        Parameters
        ----------
        score: Dict[str, Any]
            Score dictionary
        
        Returns
        -------
        str
            Formatted report
        """
        lines = [
            f"Total Score: {score['total_score']}/100",
            f"Status: {'PASS' if score['passed'] else 'FAIL'}",
        ]
        
        if score.get("error_penalty", 0) > 0:
            lines.append(f"  Error Penalty: -{score['error_penalty']}")
        
        if score.get("diff_penalty", 0) > 0:
            lines.append(f"  Diff Penalty: -{score['diff_penalty']}")
        
        if score.get("quality_bonus", 0) > 0:
            lines.append(f"  Quality Bonus: +{score['quality_bonus']}")
        
        if score.get("output_scores"):
            lines.append("  Output Scores:")
            for criterion, value in score["output_scores"].items():
                lines.append(f"    {criterion}: {value}/5.0")
        
        return "\n".join(lines)


__all__ = ["Scoring"]

