# Agent Engine Evaluation Framework

A rigorous testing system for validating the Agent Engine's accuracy, reliability, and stability.

## Structure

```
tests/
├── planning/          # Tests for planning accuracy
├── tool_selection/    # Tests for tool selection correctness
├── execution/         # Tests for execution correctness
├── end_to_end/        # Full workflow tests
├── stress/            # Stress and edge case tests
├── regression/        # Regression prevention tests
├── snapshots/         # Golden outputs for comparison
├── results/           # Test execution results (CSV)
├── test_runner.py     # Test execution engine
├── evaluator.py       # Validation logic
├── snapshot.py        # Snapshot comparison system
├── scoring.py         # Scoring and metrics
└── run_all_tests.py   # Master test runner
```

## Quick Start

1. **Start the API server:**
   ```bash
   uvicorn api.app:app --reload
   ```

2. **Run all tests:**
   ```bash
   python tests/run_all_tests.py
   ```

3. **Run with custom API URL:**
   ```bash
   python tests/run_all_tests.py --url http://localhost:8000
   ```

4. **Update snapshots:**
   ```bash
   python tests/run_all_tests.py --update-snapshots
   ```

## Test Format

Each test is a JSON file with:

```json
{
  "id": "unique-test-id",
  "category": "planning|tool_selection|execution|end_to_end|stress|regression",
  "task": "Natural language task description",
  "expected": {
    "min_steps": 5,
    "max_steps": 15,
    "required_tools": ["generate_text", "search_in_files"],
    "disallowed_tools": ["magic_tool"],
    "criteria": {
      "relevance": ">=4",
      "correctness": ">=4",
      "completeness": ">=3"
    }
  }
}
```

## Test Categories

### Planning Tests
Validate that tasks are broken down into correct, structured plans.

### Tool Selection Tests
Validate that the correct tools are selected for each subtask.

### Execution Tests
Validate that tools execute correctly with proper inputs/outputs.

### End-to-End Tests
Validate complete workflows from task to final output.

### Stress Tests
Test edge cases, ambiguous inputs, and error conditions.

### Regression Tests
Prevent previously fixed bugs from reoccurring.

## Scoring

Tests are scored on a 0-100 scale:
- Base: 100 points
- Error penalty: -10 per validation error
- Diff penalty: -5 per snapshot difference
- Quality bonus: +0-10 based on output quality

Pass threshold: 70/100

## Results

Test results are saved to `tests/results/results_TIMESTAMP.csv` with:
- Test ID and category
- Pass/fail status
- Score breakdown
- Error counts
- Execution time

## Snapshot System

Snapshots store "golden" outputs for regression testing. When outputs change, the system detects differences and flags potential regressions.

To update snapshots after intentional changes:
```bash
python tests/run_all_tests.py --update-snapshots
```

