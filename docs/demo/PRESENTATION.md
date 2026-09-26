# ArchPilot: Evidence-Driven AI Engineering Decision Agent
**Contest Presentation Outline (5 Slides)**  
**Challenge**: TechVruk AI Agentic System Challenge  
**Repository**: [https://github.com/kavita1722-sys/archpilot](https://github.com/kavita1722-sys/archpilot)

---

## Slide 1: Problem & Motivation

### The High Stakes of Systems Architecture
- Enterprise software sizing, capacity planning, and database selection carry critical financial and operational consequences.
- **The LLM Hallucination Trap**: Single-turn prompting fails systems engineers:
  - Hallucinates RAM, disk, and throughput numbers.
  - Fabricates empirical benchmarks and quotes unverified claims.
  - Leaves assumptions implicit and provides zero traceability.
  - Lacks self-verification, quality gating, or research retries.
- **Core Question**: How do we build an autonomous AI systems engineer that produces mathematically verifiable, evidence-grounded architecture decisions?

---

## Slide 2: ArchPilot Solution

### From Prompt-Response to Verifiable Agentic Engineering
- **ArchPilot**: An evidence-driven autonomous agent built on **LangGraph**, **FastAPI**, and **Streamlit**.
- **Key Innovations**:
  - **Evidence Ledger (`EV-xxx`)**: Every technical claim is indexed with canonical URL, source type, excerpt, and confidence rating.
  - **Deterministic AST Math Engine**: Eliminates arithmetic hallucination by parsing formulas into safe Abstract Syntax Trees (no `eval()`/`exec()`).
  - **Decision Ledger (`DEC-xxx`)**: Architectural decisions explicitly linked to verified evidence, constraints, assumptions, and trade-offs.
  - **Validation Center**: Automated quality gate auditing evidence coverage, math correctness, and citation integrity before finalization.
  - **Bounded Research Loop**: Automatically triggers targeted research when evidence is insufficient (strictly capped at 2 retries).

---

## Slide 3: Agentic Architecture & Workflow

### LangGraph Cyclic State Machine

```
User Task ──> [1. Normalize] ──> [2. Plan] ──> [3. Select Next Step]
                                                        │
┌───────────────────────────────────────────────────────┘
│
▼
[4. Execute Tool] (AST Calculator / Web Search / URL Fetch)
│
▼
[5. Observe] (Record Telemetry, Ingest Evidence Ledger)
│
▼
[6. Validate] (Quality Gate: Evidence, Constraints, Math, Integrity)
│
├──> [Insufficient & Retries < 2] ──> [6b. Bounded Research] ──> [4. Execute Tool]
│
└──> [Passed / Limit Reached] ──> [7. Finalize] ──> 15-Section Report (END)
```

- **Why It Is Truly Agentic**:
  - State maintained across all nodes and stored in relational database.
  - Multi-step dynamic planning with tool assignments.
  - Observations feed subsequent reasoning and evidence extraction.
  - Self-auditing quality gate with cyclical research retry loop.

---

## Slide 4: Canonical Demonstration — Private RAG Architecture

### Engineering Challenge: 100,000 PDFs, 20 Concurrent Users, Strict Privacy, Constrained Budget
1. **Task Disambiguation**: Normalized requirements, extracted 2.5M vectors (25 chunks/PDF) and 1536-dim embeddings.
2. **Deterministic Calculations**:
   - Raw Float32 RAM: $100{,}000 \times 25 \times 1536 \times 4 \div 1024^3 = \mathbf{14.31\text{ GB}}$
   - Int8 Quantized RAM: $14.31 \div 4 = \mathbf{3.58\text{ GB}}$ working set
   - Modeled Peak Throughput: $(20 \times 2) \div 60 = 0.67\text{ QPS}$ avg, $\mathbf{2.0\text{ QPS}}$ peak capacity model
   - Projected Cloud Spend: $\sim \mathbf{\$410/\text{month}}$ (based on stated 1-yr plan pricing assumptions, within $<\$600/\text{mo}$ constraint)
3. **Evidence Ledger**: Verified vendor documentation citations (`EV-001` through `EV-004`).
4. **Validation Audit**: 94% evidence coverage, 100% constraint satisfaction, 100% calculation validity, zero dangling references.
5. **Decisions Formulated**: `DEC-001` (Self-hosted Qdrant with scalar quantization) and `DEC-002` (vLLM on private VPC GPU).

---

## Slide 5: Results, Security, and Future Scope

### Production-Grade Engineering Delivery
- **Security & Safety Guardrails**:
  - 10-step SSRF defense blocking loopback, private ranges, link-local, and cloud metadata (`169.254.169.254`, `100.100.100.200`, `metadata.google.internal`).
  - External documentation quarantined in `<UNTRUSTED_EXTERNAL_DATA>` tags (prompt injection defense).
  - Bounded execution limits (`MAX_STEPS=6`, `MAX_RETRIES=2`, `MAX_ITERATIONS=16`).
- **Pluggable LLM Backends**:
  - **Mock Mode**: Deterministic offline fixtures for testing (zero cost, zero keys).
  - **Ollama Mode**: 100% private local execution.
  - **OpenAI-Compatible Mode**: Connects to OpenAI, vLLM, Groq, Together, DeepSeek.
- **Verification & Test Coverage**:
  - **71 passing automated tests** across all modules with 100% bytecode compilation pass.
  - Streamlit UI with 8 specialized operational screens.
- **Future Scope**:
  - Integration with multi-cloud cost APIs (AWS/GCP/Azure live pricing).
  - Distributed multi-worker task orchestration.
