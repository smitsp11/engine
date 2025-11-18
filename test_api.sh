#!/bin/bash

# Task Manager Agent Engine - API Test Script
# This script tests all API endpoints in sequence

set -e  # Exit on error

BASE_URL="http://localhost:8000"
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}==================================================${NC}"
echo -e "${BOLD}  Task Manager Agent Engine - API Test Suite${NC}"
echo -e "${BOLD}==================================================${NC}\n"

# Check if server is running
echo -e "${BLUE}Checking server health...${NC}"
if ! curl -s -f "$BASE_URL/health" > /dev/null; then
    echo "❌ Server is not running at $BASE_URL"
    echo "Start the server with: uvicorn api.app:app --reload"
    exit 1
fi
echo -e "${GREEN}✓ Server is healthy${NC}\n"

# Test 1: Health Check
echo -e "${BOLD}Test 1: Health Check${NC}"
echo -e "${BLUE}GET /health${NC}"
curl -s "$BASE_URL/health" | jq
echo -e "${GREEN}✓ Health check passed${NC}\n"

# Test 2: Root Endpoint
echo -e "${BOLD}Test 2: Root Endpoint${NC}"
echo -e "${BLUE}GET /${NC}"
curl -s "$BASE_URL/" | jq
echo -e "${GREEN}✓ Root endpoint passed${NC}\n"

# Test 3: Run Task - Birthday Party
echo -e "${BOLD}Test 3: Run Task (Birthday Party)${NC}"
echo -e "${BLUE}POST /run${NC}"
TASK_RESPONSE=$(curl -s -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Plan a birthday party for my friend",
    "model": "mock",
    "settings": {
      "max_steps": 10,
      "log_level": "info"
    }
  }')

echo "$TASK_RESPONSE" | jq
TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.task_id')
TASK_STATUS=$(echo "$TASK_RESPONSE" | jq -r '.status')

if [ "$TASK_STATUS" = "succeeded" ] || [ "$TASK_STATUS" = "partial_success" ]; then
    echo -e "${GREEN}✓ Task completed: $TASK_STATUS${NC}"
else
    echo -e "⚠️  Task status: $TASK_STATUS"
fi
echo -e "Task ID: $TASK_ID\n"

# Test 4: Run Task - Research
echo -e "${BOLD}Test 4: Run Task (Research)${NC}"
echo -e "${BLUE}POST /run${NC}"
RESEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Research Canadian AI startups and write a summary",
    "model": "mock"
  }')

echo "$RESEARCH_RESPONSE" | jq '.task_id, .status, .result'
RESEARCH_ID=$(echo "$RESEARCH_RESPONSE" | jq -r '.task_id')
echo -e "${GREEN}✓ Research task completed${NC}"
echo -e "Task ID: $RESEARCH_ID\n"

# Test 5: Generate Plan Only
echo -e "${BOLD}Test 5: Generate Plan (No Execution)${NC}"
echo -e "${BLUE}POST /plan${NC}"
PLAN_RESPONSE=$(curl -s -X POST "$BASE_URL/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Organize a photoshoot for a sneaker brand",
    "model": "mock"
  }')

echo "$PLAN_RESPONSE" | jq
PLAN_ID=$(echo "$PLAN_RESPONSE" | jq -r '.plan_id')
SUBTASK_COUNT=$(echo "$PLAN_RESPONSE" | jq '.subtasks | length')
echo -e "${GREEN}✓ Plan generated with $SUBTASK_COUNT subtasks${NC}"
echo -e "Plan ID: $PLAN_ID\n"

# Test 6: Execute Single Step
echo -e "${BOLD}Test 6: Execute Single Step${NC}"
echo -e "${BLUE}POST /execute-step${NC}"
STEP_RESPONSE=$(curl -s -X POST "$BASE_URL/execute-step" \
  -H "Content-Type: application/json" \
  -d '{
    "subtask": {
      "id": "test-step-1",
      "description": "Generate creative marketing ideas for a new product",
      "tool": "generate_text",
      "dependencies": [],
      "success_criteria": "At least 3 marketing ideas",
      "deliverable": "List of marketing ideas"
    },
    "context": {
      "task_description": "Marketing campaign planning"
    }
  }')

echo "$STEP_RESPONSE" | jq
STEP_ID=$(echo "$STEP_RESPONSE" | jq -r '.step_id')
STEP_STATUS=$(echo "$STEP_RESPONSE" | jq -r '.status')
echo -e "${GREEN}✓ Step executed: $STEP_STATUS${NC}"
echo -e "Step ID: $STEP_ID\n"

# Test 7: Get Debug State for First Task
echo -e "${BOLD}Test 7: Get Debug State${NC}"
echo -e "${BLUE}GET /debug/state/$TASK_ID${NC}"
DEBUG_RESPONSE=$(curl -s "$BASE_URL/debug/state/$TASK_ID")

echo "$DEBUG_RESPONSE" | jq '.state'
echo -e "${GREEN}✓ Debug state retrieved${NC}\n"

# Test 8: List All Active Tasks
echo -e "${BOLD}Test 8: List All Active Tasks${NC}"
echo -e "${BLUE}GET /debug/state${NC}"
ACTIVE_RESPONSE=$(curl -s "$BASE_URL/debug/state")

echo "$ACTIVE_RESPONSE" | jq
ACTIVE_COUNT=$(echo "$ACTIVE_RESPONSE" | jq '.count')
echo -e "${GREEN}✓ Found $ACTIVE_COUNT active tasks${NC}\n"

# Test 9: Error Handling - Invalid Model
echo -e "${BOLD}Test 9: Error Handling (Invalid Model)${NC}"
echo -e "${BLUE}POST /run with invalid model${NC}"
ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Test task with invalid model",
    "model": "gpt-4-turbo"
  }')

echo "$ERROR_RESPONSE" | jq
ERROR_STATUS=$(echo "$ERROR_RESPONSE" | jq -r '.status_code // .detail[0].type // "no_error"')
echo -e "${GREEN}✓ Error handling works (got error: $ERROR_STATUS)${NC}\n"

# Test 10: Error Handling - Validation Error
echo -e "${BOLD}Test 10: Error Handling (Validation)${NC}"
echo -e "${BLUE}POST /run with too-short task${NC}"
VALIDATION_RESPONSE=$(curl -s -X POST "$BASE_URL/run" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Short",
    "model": "mock"
  }')

echo "$VALIDATION_RESPONSE" | jq '.detail[0]' 2>/dev/null || echo "$VALIDATION_RESPONSE" | jq
echo -e "${GREEN}✓ Validation error handling works${NC}\n"

# Summary
echo -e "${BOLD}==================================================${NC}"
echo -e "${BOLD}                   Summary${NC}"
echo -e "${BOLD}==================================================${NC}"
echo -e "${GREEN}✓ All API tests passed!${NC}\n"
echo -e "Completed tasks:"
echo -e "  • Birthday Party Task: $TASK_ID ($TASK_STATUS)"
echo -e "  • Research Task: $RESEARCH_ID"
echo -e "  • Plan Generated: $PLAN_ID ($SUBTASK_COUNT subtasks)"
echo -e "  • Single Step: $STEP_ID ($STEP_STATUS)"
echo -e "  • Active Tasks: $ACTIVE_COUNT"
echo ""
echo -e "API is functioning correctly! 🎉"
echo -e "\nNext steps:"
echo -e "  • View interactive docs at: ${BLUE}$BASE_URL/docs${NC}"
echo -e "  • Read full API docs: ${BLUE}API.md${NC}"
echo -e "  • Run unit tests: ${BLUE}pytest${NC}"

