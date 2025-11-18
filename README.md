  🧠 Task Manager Agent Engine  
  A Reasoning Improvement Engine Powered by Real LLMs  
  Taking messy human tasks → simplifying → planning → rewriting → executing → fixing → finishing.  
  Because raw LLMs are powerful… but directionally challenged.

  ------------------------------------------------------
  🎯 What Is This?
  ------------------------------------------------------

  Most agents today are like:
  “Cool task! I’ll hallucinate something and hope for the best.”

  This project is the opposite.

  You’re looking at a reasoning improvement engine — a layer that sits:
  - Above an LLM (gives structure, clarity, safety)
  - Below an application (turns human intent into correct execution)

  Its entire job is to turn ambiguous, chaotic tasks into:
  ✔ structured plans
  ✔ context-rich prompts
  ✔ tool calls
  ✔ self-checks
  ✔ recoveries
  ✔ and final results that actually make sense

  In plain English:
  “If you give it a vague request, this engine will turn it into a clean to-do list and actually complete it.”

  ------------------------------------------------------
  🏗️ Architecture (Simple Version)
  ------------------------------------------------------

  User Input (messy request)
            ↓
  1) Task Simplifier
            ↓
  2) Planner (Tree-of-Thought)
            ↓
  3) Prompt Rewriter
            ↓
  4) ReAct Execution (Thought → Action → Observation → Critique)
            ↓
  5) Dynamic Replanning
            ↓
  6) Memory + State
            ↓
  Final Output (structured JSON)

  If LLMs had a personal trainer, this would be it.

  ------------------------------------------------------
  🌟 Highlight Features
  ------------------------------------------------------

  🧹 1. Task Simplification
  Cleans messy text into structured intents + constraints.

  🧠 2. Tree-of-Thought Planning
  Generates 3 plans, scores them, chooses the best.

  ✍️ 3. Prompt Rewriting (The Star Feature)
  Turns vague subtasks into 1,300+ character optimized prompts:
  - context
  - examples
  - success criteria
  - chain-of-thought guidance
  - tool-specific tips

  🤖 4. ReAct Execution Loop
  Thought → Action → Observation → Critique for every step.

  🔁 5. Dynamic Replanning
  On failure, automatically generates recovery tasks.

  🧳 6. Tool Routing + Fallbacks
  Picks the right tool and retries with alternatives if needed.

  🗃 7. Memory & State
  Stores outputs, traces, summaries, and progress.

  ------------------------------------------------------
  🧪 Example Usage
  ------------------------------------------------------

  **Python API:**
  ```python
  from agent_engine import run_agent
  result = run_agent("Plan a birthday party for my friend")
  print(result["status"])
  ```

  **REST API:**
  ```bash
  curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d '{
      "task": "Plan a birthday party for my friend",
      "model": "gemini-2.5-flash"
    }'
  ```

  Example Output (simplified):
  {
    "task": "Plan a birthday party for my friend",
    "status": "succeeded",
    "plan": [...],
    "results": [...],
    "memory": {...}
  }

  ------------------------------------------------------
  📦 Project Layout
  ------------------------------------------------------

  agent_engine/
  ├── __init__.py
  ├── agent/
  │   ├── core.py
  │   ├── planner.py
  │   ├── executor.py
  │   ├── prompt_rewriter.py
  │   ├── task_simplifier.py
  │   ├── intent_canonicalizer.py
  │   ├── memory.py
  │   ├── state.py
  │   ├── schemas.py
  │   ├── utils.py
  │   └── tools/
  │       ├── generate_text.py
  │       ├── search_in_files.py
  │       ├── modify_data.py
  │       └── save_output.py
  ├── examples/
  └── tests/

  ------------------------------------------------------
  🚀 CLI Tool
  ------------------------------------------------------

  task-agent "Plan a 3-day photoshoot for a sneaker brand"

  ------------------------------------------------------
  🎓 Design Philosophy
  ------------------------------------------------------

  LLMs don’t need to be smarter — they need better scaffolding.

  This engine adds:
  - structure
  - context
  - examples
  - constraints
  - validation
  - self-checks
  - recovery logic

  A raw LLM wings it.
  This system **thinks first**, then acts.

  ------------------------------------------------------
  📊 Features
  ------------------------------------------------------

  - **Real LLM Integration**: Uses Google Gemini 2.5 Flash for planning, generation, and evaluation
  - **Intelligent Planning**: LLM generates structured, multi-step plans with dependencies
  - **Context-Aware Execution**: Each step uses optimized prompts with full context
  - **Self-Checking**: LLM evaluates whether each step meets success criteria
  - **Dynamic Replanning**: Automatically recovers from failures with LLM-generated recovery plans

  ------------------------------------------------------
  🛠 Tests
  ------------------------------------------------------

  pytest

  ------------------------------------------------------
  🔧 Setup & Configuration
  ------------------------------------------------------

  **Required:**
  1. Install dependencies: `pip install -r requirements.txt`
  2. Set up environment variables:
     - Copy `.env.example` to `.env`: `cp .env.example .env`
     - Edit `.env` and add your Google API key:
       ```
       GOOGLE_API_KEY=your-actual-api-key-here
       ```
     - Get your API key from: https://makersuite.google.com/app/apikey
     - **Important**: Never commit your `.env` file to version control. It's already in `.gitignore`.
  3. Run the API: `uvicorn api.app:app --reload`

  **Model Options:**
  - Default: `gemini-2.5-flash` (cost-effective, fast)
  - High quality: `gemini-2.5-pro` (better reasoning, slower)

  ------------------------------------------------------
  📈 Roadmap (Next Steps)
  ------------------------------------------------------

  - Step-level self-reflection
  - Backtracking (undo + retry)
  - Multi-agent execution per intent
  - Long-term memory summarization
  - Support for additional LLM providers

  ------------------------------------------------------
  📝 License
  ------------------------------------------------------

  MIT
