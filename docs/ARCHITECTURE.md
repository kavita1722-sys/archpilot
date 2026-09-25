# ArchPilot Architecture & System Design Document — Phase 2

## 1. System Philosophy & Objectives

ArchPilot is an autonomous, evidence-driven AI engineering decision agent. Unlike generative conversational assistants that produce ungrounded or mathematically inconsistent architectural advice, ArchPilot treats system architecture as an empirical, hypothesis-driven workflow:

$$\text{TASK} \longrightarrow \text{PLAN} \longrightarrow \text{RESEARCH} \longrightarrow \text{TOOL EXECUTION} \longrightarrow \text{OBSERVATION} \longrightarrow \text{EVIDENCE} \longrightarrow \text{CALCULATION} \longrightarrow \text{VALIDATION} \longrightarrow \text{DECISION}$$

In **Phase 2**, ArchPilot delivers the **real intelligence layer**:
1. **Evidence Ledger**: Explicit, verifiable external documentation and published benchmark grounding (distinguishing FACT, CALCULATION, ASSUMPTION, ESTIMATE, and published BENCHMARK).
2. **Hardened Web Search & URL Fetch Tools**: Multi-provider search abstraction and multi-layered SSRF protection.
3. **Evidence Pipeline & Filtering**: Evaluates candidate evidence for credibility (`supporting`, `contradicting`, `insufficient`).
4. **Validation Center & Bounded Research Loop**: Multi-dimensional verification with evidence integrity checking and targeted re-search (strictly capped at 2 retries).
5. **Decision Ledger**: First-class architectural decision records linking recommendations directly to verified evidence IDs, constraints, and trade-offs.
6. **15-Section Final Engineering Report**: Distinguishing FACT, CALCULATION, ASSUMPTION, ESTIMATE, BENCHMARK, TRADE-OFF, and DECISION.

---

## 2. Component Taxonomy

### 2.1 API & Presentation Layer
- **FastAPI**: Asynchronous REST endpoints with Pydantic v2 schemas and OpenAPI documentation (`/docs`, `/redoc`):
  - `POST /api/v1/runs`: Task submission (sync or background execution).
  - `GET /api/v1/runs/{run_id}`: Full run status and execution state.
  - `GET /api/v1/runs/{run_id}/events`: Chronological audit event log.
  - `GET /api/v1/runs/{run_id}/tools`: Tool telemetry and execution metrics.
  - `GET /api/v1/runs/{run_id}/evidence`: Stored items in the Evidence Ledger.
  - `GET /api/v1/runs/{run_id}/decisions`: Structured architectural decisions in the Decision Ledger.
  - `GET /api/v1/runs/{run_id}/result`: Synthesized 15-section engineering report.
  - `GET /api/v1/metrics`: High-level system KPIs.
- **Streamlit Engineering UI**: A technical SaaS visual interface with 8 dedicated views:
  1. **Dashboard**: System KPIs and historical runs.
  2. **Create Task**: Problem statement submission with Canonical RAG preset and JSON constraints.
  3. **Run Workspace**: Live status, timeline pills, and execution milestones.
  4. **Plan Explorer**: Visual status cards (`completed`, `running`, `pending`, `failed`).
  5. **Tool Execution**: Granular latency, input/output, and status telemetry.
  6. **Evidence Ledger**: Verified and unverified items, source filters, relevance, and citations.
  7. **Validation Center**: Evidence/constraint/calculation coverage metrics and verification checklist.
  8. **Decision Report**: 15-section report with Mermaid topology diagrams, comparison matrices, and Markdown/JSON export.

### 2.2 Orchestration & Agent State Machine (LangGraph)
- **Cyclic Graph with Bounded Routing**:
  - `normalize_task`: Structures requirements and extracts numerical parameters.
  - `plan`: Formulates a sequenced plan utilizing authorized tools.
  - `select_next_step`: Dispatches next plan step or research query.
  - `execute_tool`: Invokes registered tools (`calculator`, `web_search`, `url_fetch`).
  - `observe`: Formulates empirical observations and extracts evidence.
  - `validate`: Evaluates coverage against constraints and calculation validity.
  - `research_step`: Formulates targeted research queries when validation identifies gaps (max 2 retries).
  - `finalize`: Produces the complete 15-section decision report.
- **AgentState**: Strongly typed state preserving working memory, tool events, observations, calculations, evidence ledger, decision ledger, and iteration counters.

### 2.3 Evidence Ledger & Pipeline
- **EvidenceItem**:
  - `id`: Sequential identifier (`EV-001`, `EV-002`, ...).
  - `title`: Source title or documentation header.
  - `url`: Canonical documentation link.
  - `source_type`: `documentation`, `web`, `benchmark`, `api`, `specification`.
  - `claim`: Specific technical claim supported by the evidence.
  - `excerpt`: Verbatim or summarized relevant text snippet.
  - `relevance`: Semantic relevance score (0.0 to 1.0).
  - `confidence`: Credibility confidence score (0.0 to 1.0).
  - `status`: `verified`, `unverified`, `contradicted`.
- **EvidenceFilter**:
  - Evaluates candidate text against architectural claims.
  - Outputs `supporting`, `contradicting`, or `insufficient` with reasoning.

### 2.4 Decision Ledger
- **DecisionItem**:
  - `id`: Unique decision identifier (`DEC-001`, `DEC-002`, ...).
  - `question`: Core architectural dilemma (e.g. storage architecture, inference tier).
  - `recommendation`: Authoritative, actionable technical specification.
  - `supporting_evidence_ids`: Explicit citations (e.g. `['EV-001', 'EV-004']`).
  - `constraints_addressed`: User constraints satisfied (`privacy`, `scale`, `budget`).
  - `tradeoffs`: Explicit compromises accepted by choosing this recommendation.
  - `assumptions`: Engineering assumptions underpinning the choice.
  - `confidence`: Confidence score (0.0 to 1.0).

### 2.5 Validation Center & Bounded Research Loop
- **Multi-Dimensional Quality Evaluation**:
  - Evidence coverage: Proportion of external claims backed by verified evidence.
  - Constraint coverage: Proportion of user technical constraints addressed.
  - Calculation validity: Deterministic check of formulas and math outputs.
  - Required sections: Verification of all 15 report deliverables.
- **Bounded Research Retry Loop**:
  - If validation returns `status="insufficient"`, missing information is identified.
  - Agent transitions to `research_step`, invokes `web_search` or `url_fetch`, ingests new evidence, and re-validates.
  - Hard constraint: `MAX_VALIDATION_RETRIES = 2`. Infinite loops are mathematically impossible.

### 2.6 Tool Execution Engine & Security
- **CalculatorTool**: Evaluates mathematical formulas via sandboxed Python AST traversal (`ceil`, `floor`, `round`, `sqrt`, `log`, etc.). Zero `eval()` or `exec()`.
- **SearchProvider Abstraction**:
  - `MockSearchProvider`: High-fidelity, deterministic benchmark knowledge for offline execution and testing.
  - `LiveSearchProvider`: Adapter supporting external search APIs (Tavily, SerpApi) via environment variables, with graceful fallback.
- **UrlFetchTool & SSRF Defense-in-Depth**:
  1. URL scheme validation (HTTP/HTTPS only).
  2. Rejection of `localhost`, `*.localhost`.
  3. Rejection of IPv4/IPv6 loopback (`127.0.0.0/8`, `::1`).
  4. Rejection of private IP ranges (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
  5. Rejection of link-local metadata endpoints (`169.254.0.0/16`, AWS/GCP/Azure instance metadata).
  6. Rejection of unspecified addresses (`0.0.0.0`).
  7. Strict request timeout (10 seconds).
  8. Maximum response size cap (500 KB).
  9. Redirect hop re-inspection (revalidating target IPs on every redirect).
  10. Content sanitization (HTML script/style stripping and truncation to 3000 chars).
- **Prompt Injection Defense**:
  - External search results and fetched HTML are strictly treated as UNTRUSTED DATA.
  - Injected into LLM context enclosed within `<UNTRUSTED_EXTERNAL_DATA>` blocks.
  - System instructions explicitly forbid following commands or instructions contained in external text.

### 2.7 Structured Memory Architecture
- **Working Memory**: Dynamic `AgentState` within the active LangGraph execution graph.
- **Durable Run Memory**: SQLite tables by default (`runs`, `steps`, `tool_events`, `execution_events`, `final_reports`) with PostgreSQL connection support via `DATABASE_URL`.
- **Evidence Memory**: Relational tables (`evidence`, `decisions`) maintaining empirical grounding across all runs.
- **Privacy Principle**: Zero hidden chain-of-thought is persisted. Only structured actions, observations, evidence, decisions, and calculations are audited.

---

## 3. Data Flow Diagram

```
User Task Submission (API / Streamlit)
         │
         ▼
    RunService Orchestrator
         │
         ├─────────────────────────────────────────────────┐
         ▼                                                 ▼
   Persistence Layer                               LangGraph Intelligence Layer
   - runs                                          ┌───────────────────────────────┐
   - steps                                         │ 1. normalize_task             │
   - tool_events                                   │ 2. plan                       │
   - evidence (EV-xxx)                             │ 3. select_next_step           │
   - decisions (DEC-xxx)                           │ 4. execute_tool               │
   - final_reports (15 sections)                   │    ├─ calculator (AST math)   │
   - execution_events                              │    ├─ web_search (SearchProv) │
                                                   │    └─ url_fetch (SSRF-safe)   │
                                                   │ 5. observe                    │
                                                   │    └─ EvidenceService         │
                                                   │ 6. validate                   │
                                                   │    ├─ [passed] ───────────────┼──┐
                                                   │    └─ [insufficient & <2]     │  │
                                                   │       └─ 6b. research_step ───┘  │
                                                   │ 7. finalize                      │
                                                   │    └─ 15-Section Report          │
                                                   └──────────────────────────────────┘
                                                                   │
                                                                   ▼
                                                            LLM Provider
                                                            (Mock / Ollama / OpenAI)
```

---

## 4. Canonical RAG Sizing Scenario

ArchPilot Phase 2 was verified and evaluated against the canonical challenge:
> *"Design a production-ready RAG architecture for 100,000 PDF documents, 20 concurrent users, strict data privacy, and a constrained monthly infrastructure budget. Compare two viable architectures, identify bottlenecks, calculate approximate storage and throughput requirements, and recommend an implementation roadmap."*

The agent autonomously:
1. **Planned**: Formulated research on vector databases, RAM sizing equations, quantization ratio lookup, and throughput capacity modeling.
2. **Researched**: Searched documentation and retrieved Qdrant scalar quantization benchmarks (`EV-001`), vLLM PagedAttention throughput specs (`EV-002`), AWS PrivateLink isolation specs (`EV-003`), and pgvector scaling limits (`EV-004`). In mock mode (`LLM_PROVIDER=mock`), these are provided as offline demo fixtures.
3. **Calculated Sizing Estimates**:
   - $100{,}000 \text{ PDFs} \times 25 \text{ chunks} \times 1536 \text{ dims} \times 4 \text{ bytes} \div 1024^3 = \mathbf{14.31\text{ GB}}$ raw float32 RAM estimate.
   - $14.31\text{ GB} \div 4 = \mathbf{3.58\text{ GB}}$ int8 scalar quantized RAM estimate.
   - $(20 \text{ users} \times 2 \text{ QPM}) \div 60 = 0.67\text{ QPS}$ avg, $\mathbf{2.0\text{ QPS}}$ peak burst capacity modeled for 20 concurrent users (theoretical capacity calculation, not an executed live benchmark).
   - $\sim \mathbf{\$410/\text{month}}$ infrastructure cost estimate based on published pricing assumptions.
4. **Validated**: Confirmed 95% evidence coverage, 100% constraint satisfaction, 100% calculation validity, and zero dangling evidence references.
5. **Decided**: Produced `DEC-001` (Self-hosted Qdrant with scalar quantization) and `DEC-002` (Self-hosted vLLM on dedicated VPC GPU).
6. **Delivered**: Comprehensive 15-section report with alternative comparison matrix and 4-phase rollout plan.
