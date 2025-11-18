  🧠 Task Manager Agent Engine  
  A Reasoning Improvement Engine for LLMs  
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

  from agent_engine import run_agent
  result = run_agent("Plan a birthday party for my friend")
  print(result["final_status"])

  Example Output (simplified):
  {
    "task": "Plan a birthday party for my friend",
    "final_status": "SUCCEEDED",
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
  📊 Performance (Synthetic Benchmarks)
  ------------------------------------------------------

  | Task            | Subtasks | Success Rate | Avg Prompt Size |
  |-----------------|----------|--------------|------------------|
  | Party Planning  | 5        | 100%         | 1,350 chars      |
  | Research Task   | 5        | 100%         | 1,280 chars      |

  ------------------------------------------------------
  🛠 Tests
  ------------------------------------------------------

  pytest

------------------------------------------------------
🌐 API Service Layer (NEW!)
------------------------------------------------------

The agent engine now has a complete FastAPI service layer!

**Quick Start:**
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn api.app:app --reload

# Open interactive docs
open http://localhost:8000/docs
```

**Available Endpoints:**
- `POST /run` - Execute a complete task
- `POST /plan` - Generate a plan without execution
- `POST /execute-step` - Run a single subtask
- `GET /health` - Health check
- `GET /debug/state/{task_id}` - View internal state

**Test the API:**
```bash
# Run the test script
./test_api.sh

# Or manually
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Plan a birthday party", "model": "mock"}'
```

**Documentation:**
- 📖 **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- 📚 **[API.md](API.md)** - Complete API documentation with examples
- 🧪 **[test_api.sh](test_api.sh)** - Automated test script

**What You Get:**
- ✅ RESTful API with FastAPI
- ✅ Comprehensive request/response schemas (Pydantic)
- ✅ Structured logging (structlog)
- ✅ Error handling and validation
- ✅ Mock reasoning model for testing
- ✅ Integration tests (pytest)
- ✅ Interactive Swagger UI docs
- ✅ curl and Postman examples

**API Architecture:**
```
api/
├── app.py              # FastAPI application
├── models/
│   └── mock_model.py   # Mock LLM for testing
└── schemas/
    ├── run_request.py  # Request schemas
    └── run_response.py # Response schemas
```

------------------------------------------------------
📈 Roadmap (Next Steps)
------------------------------------------------------

**Phase 1: Core Engine** ✅ COMPLETE
- [x] Task planning and decomposition
- [x] ReAct execution loop
- [x] Tool routing and fallbacks
- [x] Memory and state tracking
- [x] Dynamic replanning

**Phase 2: API Layer** ✅ COMPLETE
- [x] FastAPI service
- [x] Request/response schemas
- [x] Mock reasoning model
- [x] Integration tests
- [x] API documentation

**Phase 3: Real LLM Integration** 🔄 IN PROGRESS
- [ ] OpenAI integration
- [ ] Anthropic Claude integration
- [ ] Rate limiting and caching
- [ ] Streaming responses

**Phase 4: Persistence & Scale** 📋 PLANNED
- [ ] SQLite/PostgreSQL storage
- [ ] Task resumption
- [ ] Job queue (Celery/RQ)
- [ ] Distributed execution

**Phase 5: Frontend & UX** 📋 PLANNED
- [ ] React/Next.js dashboard
- [ ] Real-time task monitoring (WebSockets)
- [ ] Visual plan editor
- [ ] Agent playground

**Phase 6: Production Ready** 📋 PLANNED
- [ ] Docker containerization
- [ ] Deploy to Render/Fly.io
- [ ] Authentication & authorization
- [ ] Rate limiting & quotas
- [ ] Monitoring & observability
- [ ] CI/CD pipeline

------------------------------------------------------
🧪 Testing
------------------------------------------------------

**Run Unit Tests:**
```bash
pytest
```

**Run with Coverage:**
```bash
pytest --cov=agent_engine --cov=api --cov-report=html
```

**Test API Endpoints:**
```bash
# Start server first
uvicorn api.app:app --reload

# Run test suite
./test_api.sh
```

**Specific Test Files:**
```bash
pytest tests/test_planner.py -v       # Planner tests
pytest tests/test_executor.py -v      # Executor tests
pytest tests/test_api.py -v           # API integration tests
pytest tests/test_api_mock_model.py -v # Mock model tests
```

------------------------------------------------------
📝 License
------------------------------------------------------

MIT

