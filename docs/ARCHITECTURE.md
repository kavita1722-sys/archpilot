# ArchPilot Architecture & System Design Document

## 1. System Philosophy

ArchPilot is engineered to bridge the divide between unstructured natural language reasoning and rigorous, deterministic system engineering. Unlike typical generative chatbots that provide hand-wavy or mathematically flawed architectural suggestions, ArchPilot treats architecture design as an empirical, hypothesis-driven workflow:

$$\text{Task} \longrightarrow \text{Normalization} \longrightarrow \text{Planning} \longrightarrow \text{Tool Invocation} \longrightarrow \text{Observation} \longrightarrow \text{Validation} \longrightarrow \text{Synthesis}$$

---

## 2. Component Taxonomy

### 2.1 API & Presentation Layer
- **FastAPI**: Exposes standardized asynchronous REST endpoints with automated OpenAPI (`/docs`) and ReDoc (`/redoc`) documentation. Includes strict Pydantic v2 validation and structured domain error handling without leaking stack traces.
- **Streamlit SaaS Dashboard**: Provides interactive run initiation, real-time stage progression pills, step-by-step tool telemetry inspection, and the final decision document with interactive traceability cards.

### 2.2 Orchestration & Agent State Machine
- **LangGraph StateGraph**: Models the workflow as a cyclic state machine with bounded conditional routing.
- **AgentState**: A strongly typed schema tracking `run_id`, `task`, `constraints`, `normalized_task`, `plan`, `current_step_id`, `current_step_index`, `observations`, `tool_events`, `calculations`, `validation`, `final_result`, and execution iteration counters.

### 2.3 Execution Guardrails & Policies
- `MAX_STEPS = 6`: Plans cannot exceed 6 discrete steps.
- `MAX_TOOL_RETRIES = 2`: Unsuccessful tool invocations are capped to 2 retries.
- `MAX_VALIDATION_RETRIES = 2`: Re-evaluations are strictly bounded.
- `MAX_ITERATIONS = 12`: Guarantees graph termination and prevents infinite loops.
- `Tool Allowlist`: Enforces that only registered, authorized tools can be executed.

### 2.4 Tool Execution Engine
- **CalculatorTool**: Evaluates mathematical expressions using Python's `ast` parser in `eval` mode.
  - Recursively checks node types (`Constant`, `BinOp`, `UnaryOp`, `Call`).
  - Explicitly restricts functions to safe math primitives (`ceil`, `floor`, `round`, `sqrt`, `min`, `max`, `abs`, `log`, etc.).
  - Employs power limit bounds (`exponent <= 100`) to prevent computational exhaustion attacks.
  - Zero usage of Python's dangerous `eval()` or `exec()`.

### 2.5 Multi-Backend LLM Provider Abstraction
- **LLMProvider (ABC)**: Core abstract interface.
- **MockLLMProvider**: Fast, deterministic, domain-aware mock provider for CI/CD and offline evaluation.
- **OllamaProvider**: Direct REST communication with local Ollama daemon for local inference (e.g. Llama 3.2, DeepSeek).
- **OpenAICompatibleProvider**: Standard chat completions with JSON schema validation for OpenAI, Groq, vLLM, and OpenRouter endpoints.

### 2.6 Persistence Layer
- **SQLAlchemy 2.0**: Relational mapping supporting SQLite (Phase 1) and PostgreSQL (Production).
- **Relational Models**:
  - `runs`: High-level run state, timestamps, error records, and final deliverables.
  - `steps`: Individual plan steps with status tracking (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`).
  - `tool_events`: Granular execution telemetry, inputs, outputs, execution duration, and errors.
  - `execution_events`: Chronological audit log of all state transitions.

---

## 3. Data Flow Diagram

```
User / Web Client / CLI
         │
         ▼
    FastAPI Router (/api/v1/runs)
         │
         ▼
    RunService Orchestrator
         │
         ├─────────────────────────────────────────┐
         ▼                                         ▼
   SQLAlchemy DB                           LangGraph Agent
   - runs                                  ┌───────────────────────────────┐
   - steps                                 │ 1. normalize_task             │
   - tool_events                           │ 2. plan                       │
   - execution_events                      │ 3. select_next_step           │
                                           │ 4. execute_tool (AST Math)    │
                                           │ 5. observe                    │
                                           │ 6. validate                   │
                                           │ 7. finalize                   │
                                           └───────────────────────────────┘
                                                           │
                                                           ▼
                                                   LLM Provider
                                                   (Mock / Ollama / OpenAI)
```

---

## 4. Security Principles

1. **Defense-in-Depth against Command Injection**: Input prompts are scanned for dangerous execution syntax (`__import__`, `subprocess`, `os.system`, shell invocations).
2. **Safe Expression Parsing**: Mathematical expressions are strictly parsed via Python AST trees with zero access to globals, builtins, or attribute chains.
3. **No Hardcoded Secrets**: All configuration is managed through Pydantic Settings and `.env`.
4. **Information Leakage Prevention**: Production exception handlers return standardized typed error responses without exposing server traces.
