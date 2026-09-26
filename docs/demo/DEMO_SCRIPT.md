# ArchPilot: 5-Minute Contest Demonstration Video Script
**Challenge**: TechVruk AI Agentic System Challenge  
**Target Duration**: 4 minutes 50 seconds (Under 5 minutes)  
**Speaker**: Systems Engineer / Presenter  
**Screen Display**: Streamlit SaaS Dashboard (`http://localhost:8501`) & Terminal

---

### [0:00 – 0:20] Segment 1: Problem & Introduction
*Visual: Streamlit Dashboard landing page (`http://localhost:8501`) displaying global metrics.*

> **Presenter**:  
> "Hello! Today we present **ArchPilot**, an evidence-driven AI agent designed for high-stakes software and systems architecture decisions.  
> Standard single-prompt LLMs fail when sizing enterprise systems—they hallucinate RAM and disk numbers, fabricate benchmarks, and offer zero traceability.  
> ArchPilot solves this by replacing one-shot prompts with a verified LangGraph agentic loop: Plan, Act, Observe, Validate, and Respond."

---

### [0:20 – 0:45] Segment 2: Enter Engineering Task
*Visual: Click on **Create Task** in the sidebar. Select the Canonical RAG preset or paste the task.*

> **Presenter**:  
> "Let's submit our challenge:  
> *'Design an architecture for a private RAG platform that must ingest 100,000 PDF documents, support 20 concurrent users, maintain strict data privacy, and stay within a constrained infrastructure budget. Compare architecture alternatives, calculate capacity requirements, identify risks, and provide an implementation roadmap.'*  
> We submit the task. Notice ArchPilot immediately initializes a PENDING run and triggers our compiled LangGraph state machine."

---

### [0:45 – 1:20] Segment 3: Show Generated Plan
*Visual: Navigate to **Run Workspace** and click on **Plan Explorer** tab.*

> **Presenter**:  
> "The first two LangGraph nodes execute: `normalize_task` disambiguates requirements and extracts quantitative variables.  
> Then the `plan` node formulates a bounded, multi-step execution plan.  
> Look at the plan: it assigns specific authorized tools to each step:
> - Step 1: Research vector DB memory footprint and quantization via `web_search`.
> - Step 2: Calculate raw vector RAM for 2.5 million vectors via `calculator`.
> - Step 3: Fetch official Qdrant quantization docs via `url_fetch`.
> - Step 4: Calculate quantized vector RAM via `calculator`.
> - Step 5: Calculate query throughput model via `calculator`.  
> No step is vague; each has concrete inputs and measurable success criteria."

---

### [1:20 – 2:00] Segment 4: Show Tool Execution (Calculator, Web Search, URL Fetch)
*Visual: Click on **Tool Execution** tab. Expand individual tool execution cards.*

> **Presenter**:  
> "Now the agent enters the execution cycle. In the **Tool Execution** ledger:
> 1. First, `web_search` queries documentation for memory sizing benchmarks and returns normalized technical excerpts in 14 milliseconds.
> 2. Next, `calculator` executes deterministic AST arithmetic: $100{,}000 \times 25 \times 1536 \times 4 \div 1024^3$, outputting exactly 14.31 GB raw vector RAM. No `eval()` or `exec()` is ever used.
> 3. Then, `url_fetch` retrieves documentation from `https://qdrant.tech` under strict 10-step SSRF protection—blocking loopback, private IPs, link-local addresses, and cloud metadata endpoints.
> 4. Finally, the calculator divides 14.31 by 4 to compute quantized memory at 3.58 GB.  
> Every tool call logs start time, execution latency, and exact status."

---

### [2:00 – 2:35] Segment 5: Show Observations & Evidence Ledger
*Visual: Click on **Evidence Ledger** tab.*

> **Presenter**:  
> "As tools complete, the `observe` node processes outputs and populates the **Evidence Ledger**.  
> Notice evidence items `EV-001` through `EV-004`:
> - Each records canonical URL, source type, claim, verbatim excerpt, relevance, and confidence score.
> - We strictly enforce epistemic boundaries: verified documentation is labeled **FACT**, computed formulas are **CALCULATION**, technical baselines are **ASSUMPTION**, and projected costs are **ESTIMATE**. Theoretical models are never misrepresented as live benchmarks."

---

### [2:35 – 3:10] Segment 6: Show Validation Center & Bounded Retry
*Visual: Click on **Validation Center** tab.*

> **Presenter**:  
> "Before generating any recommendation, the workflow enters the **Validation Center**.  
> The agent audits its own state:
> - Evidence coverage: 94% of claims backed by verified documentation.
> - Constraint coverage: 100% of user constraints addressed.
> - Calculation validity: 100% verified AST formulas.
> - Evidence Integrity: Confirms zero dangling references.  
> If evidence were insufficient, the graph would dispatch a bounded research retry—capped strictly at 2 retries to eliminate infinite loops. Here, validation passes."

---

### [3:10 – 3:50] Segment 7: Show Final Engineering Decision
*Visual: Click on **Decision Report** tab. Scroll through the executive summary and decisions.*

> **Presenter**:  
> "Now we view the final synthesized **15-Section Engineering Decision Report**:
> - In Section 1, the Executive Summary recommends a self-hosted private VPC architecture pairing Qdrant with vLLM.
> - In Section 11, the Decision Ledger records `DEC-001` (Qdrant with scalar quantization) and `DEC-002` (vLLM on private VPC GPU).
> - Crucially, every decision cites verified evidence IDs (`EV-001`, `EV-002`) and explicit trade-offs. If a citation were missing, our integrity filter would drop it rather than hallucinating evidence."

---

### [3:50 – 4:20] Segment 8: Show Architecture Comparison, Trade-offs & Risks
*Visual: Scroll to Comparison Matrix, Capacity Calculations, Trade-offs, and Roadmap.*

> **Presenter**:  
> "ArchPilot evaluates alternatives in Section 8: comparing the Recommended Qdrant architecture against PostgreSQL with pgvector (Alternative A) and AWS OpenSearch Serverless (Alternative B) across Cost, Latency, Privacy, and Maintenance.  
> Section 9 details deterministic capacity formulas.  
> Section 12 captures explicit trade-offs—acknowledging container management overhead in exchange for zero data egress.  
> Sections 13 and 14 provide failure mode mitigations and an actionable 4-phase implementation roadmap."

---

### [4:20 – 4:40] Segment 9: Explain Agentic Architecture & State
*Visual: Show the LangGraph architecture diagram in README or presentation.*

> **Presenter**:  
> "What makes ArchPilot genuinely agentic?  
> It is not a prompt wrapper. Execution is driven by a LangGraph cyclic state machine. State is persisted in relational tables across every node. The agent reasons about intermediate observations, chooses tools dynamically, validates its own findings, and can loop back to research when gaps exist."

---

### [4:40 – 5:00] Segment 10: Closing
*Visual: Show GitHub repository page (`https://github.com/kavita1722-sys/archpilot`) and terminal running test suite (71 passing tests).*

> **Presenter**:  
> "ArchPilot runs out-of-the-box with zero paid API keys in Mock mode, and seamlessly connects to Ollama or OpenAI-compatible endpoints. With 71 passing automated tests, safe AST math, and full SSRF security, ArchPilot delivers reliable, evidence-backed AI systems engineering.  
> Thank you!"
