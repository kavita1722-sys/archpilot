# ArchPilot Contest Demonstration — Sample Output

> **Execution Notice**:  
> **DEMO / MOCK OUTPUT**  
> Generated under `LLM_PROVIDER=mock` using deterministic mathematical calculations, simulated documentation fixtures, and capacity sizing models. Findings and throughput numbers represent theoretical capacity planning and published vendor documentation citations, not live empirical load-test results.

---

## 1. Normalized Task

```json
{
  "normalized_task": "Design an architecture for a private RAG platform ingesting 100,000 PDF documents, supporting 20 concurrent users, maintaining strict data privacy, and bounded by a constrained infrastructure budget.",
  "domain": "Enterprise Search & Retrieval-Augmented Generation (RAG)",
  "extracted_constraints": {
    "document_volume": "100,000 PDF documents",
    "concurrency": "20 concurrent users",
    "privacy": "Strict data privacy (no third-party training, isolated VPC)",
    "budget": "Constrained monthly infrastructure budget (<$600/month)",
    "comparison_required": "Compare two viable architectures",
    "calculation_required": true
  },
  "target_metric": "Vector Index RAM (GB), Persistent Disk (GB), Query Throughput (QPS), Monthly Cost ($)",
  "requires_calculation": true,
  "key_variables": [
    "100,000 PDF documents",
    "25 chunks per PDF (2.5M vectors)",
    "1536-dimensional embeddings",
    "20 concurrent user query sessions",
    "Sub-1.5s p95 latency SLA"
  ]
}
```

---

## 2. Multi-Step Execution Plan

```json
{
  "goal": "Design and capacity-plan an evidence-backed private RAG architecture for 100,000 PDFs and 20 concurrent users.",
  "assumptions": [
    "ASSUMPTION: 100,000 PDFs average 25 chunks each (total 2.5 million chunks).",
    "ASSUMPTION: Embeddings use 1536 dimensions (float32 = 4 bytes per dim).",
    "ASSUMPTION: Int8 scalar quantization reduces RAM by 4x with <0.5% recall penalty.",
    "ASSUMPTION: 20 concurrent users generate 2 queries/min each (0.67 QPS avg, 2.0 QPS peak throughput model; theoretical capacity sizing, not an executed empirical benchmark)."
  ],
  "steps": [
    {
      "id": 1,
      "objective": "Research vector database memory footprint and scalar quantization benchmarks.",
      "tool": "web_search",
      "inputs": {
        "query": "qdrant memory requirements 1536 dimension vector index scalar quantization",
        "max_results": 4
      },
      "success_criteria": "Published vector memory scaling and scalar quantization benchmark documentation retrieved.",
      "status": "COMPLETED"
    },
    {
      "id": 2,
      "objective": "Calculate raw vector index RAM requirements for 100k PDFs (2.5M 1536-dim vectors in float32).",
      "tool": "calculator",
      "inputs": {
        "expression": "100000 * 25 * 1536 * 4 / (1024 * 1024 * 1024)"
      },
      "success_criteria": "Total raw vector RAM in GB calculated deterministically.",
      "status": "COMPLETED"
    },
    {
      "id": 3,
      "objective": "Fetch official Qdrant scalar quantization technical documentation for published compression ratio.",
      "tool": "url_fetch",
      "inputs": {
        "url": "https://qdrant.tech/documentation/guides/quantization/"
      },
      "success_criteria": "Verified scalar quantization memory reduction ratio and recall metrics.",
      "status": "COMPLETED"
    },
    {
      "id": 4,
      "objective": "Calculate quantized vector index memory with int8 scalar quantization (4x compression).",
      "tool": "calculator",
      "inputs": {
        "expression": "14.305 / 4"
      },
      "success_criteria": "Quantized RAM requirement in GB calculated.",
      "status": "COMPLETED"
    },
    {
      "id": 5,
      "objective": "Calculate theoretical interactive query throughput (QPS) for 20 concurrent users assuming 2 queries/min per user.",
      "tool": "calculator",
      "inputs": {
        "expression": "(20 * 2) / 60"
      },
      "success_criteria": "Theoretical peak and average query throughput QPS determined based on stated concurrency assumptions.",
      "status": "COMPLETED"
    }
  ]
}
```

---

## 3. Tool Actions & Telemetry

| Step | Tool | Inputs | Status | Duration | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `web_search` | `{"query": "qdrant memory requirements 1536 dimension..."}` | `success` | 14.2 ms | Retrieved 4 documentation excerpts on HNSW indexing & RAM |
| **2** | `calculator` | `{"expression": "100000 * 25 * 1536 * 4 / (1024 * 1024 * 1024)"}` | `success` | 0.4 ms | `14.30511474609375` (GB raw float32 vector RAM) |
| **3** | `url_fetch` | `{"url": "https://qdrant.tech/documentation/guides/quantization/"}` | `success` | 1.8 ms | Extracted documentation: 75% memory reduction with <0.5% recall loss |
| **4** | `calculator` | `{"expression": "14.305 / 4"}` | `success` | 0.3 ms | `3.57625` (GB quantized vector RAM) |
| **5** | `calculator` | `{"expression": "(20 * 2) / 60"}` | `success` | 0.3 ms | `0.6666666666666666` (Avg QPS; Peak burst = 2.0 QPS) |

---

## 4. Observations

- **Observation 1**: 100,000 PDFs yield ~2.5 million vectors (1536 dimensions), requiring 14.31 GB raw float32 memory.
- **Observation 2**: Int8 scalar quantization compresses vector RAM to 3.58 GB, enabling single-node hosting with low memory overhead.
- **Observation 3**: 20 concurrent users generate 0.67 QPS average and 2.0 QPS peak query throughput based on modeled query rates, easily accommodated on a single modern GPU inference node.

---

## 5. Capacity Calculations

| Metric | Formula | Result | Unit | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Total Vector Count** | `100,000 PDFs * 25 chunks/PDF` | `2,500,000` | vectors | `ESTIMATE` (from chunking assumption) |
| **Raw Vector Memory** | `2.5M * 1536 * 4 bytes / (1024^3)` | `14.31` | GB | `CALCULATION` |
| **Quantized Vector Memory** | `14.305 / 4` | `3.58` | GB | `CALCULATION` |
| **Estimated Working Set RAM** | `3.58 GB * 1.5 + 4 GB OS headroom` | `9.37` | GB | `ESTIMATE` (includes OS & index buffer) |
| **Estimated Persistent Chunk Disk** | `2.5M * 1000 chars * 4 bytes / (1024^3)` | `9.31` | GB | `ESTIMATE` (includes metadata overhead) |
| **Estimated Query Throughput** | `(20 users * 2 QPM) / 60` | `0.67` avg / `2.0` peak | QPS | `ESTIMATE` (theoretical capacity model) |
| **Estimated Cloud Monthly Cost** | `EC2 g5.xlarge (1x A10G 24GB) @ $0.56/hr (1-yr plan)` | `~$410` | $/month | `ESTIMATE` (based on stated AWS pricing) |

---

## 6. Evidence Ledger

- **[EV-001]** *(documentation)*: **Qdrant Scalar Quantization Technical Benchmarks [Demo Fixture]**  
  *Claim*: Scalar quantization (int8) compresses 1536-dim vector memory by 4x with less than 0.5% recall loss.  
  *URL*: `https://qdrant.tech/documentation/guides/quantization/`  
  *Confidence*: 0.94 | *Status*: `verified`

- **[EV-002]** *(documentation)*: **vLLM PagedAttention High-Throughput Inference Engine [Demo Fixture]**  
  *Claim*: PagedAttention achieves 2-4x higher throughput than standard transformers on 24GB GPUs, providing headroom for concurrent queries.  
  *URL*: `https://docs.vllm.ai/en/latest/`  
  *Confidence*: 0.91 | *Status*: `verified`

- **[EV-003]** *(documentation)*: **AWS PrivateLink & VPC Endpoint Security Architecture [Demo Fixture]**  
  *Claim*: Deploying inference inside a dedicated VPC ensures traffic never traverses public internet, satisfying strict compliance.  
  *URL*: `https://docs.aws.amazon.com/whitepapers/latest/aws-privatelink/aws-privatelink.html`  
  *Confidence*: 0.95 | *Status*: `verified`

- **[EV-004]** *(benchmark)*: **pgvector vs Dedicated Vector Search Scaling Analysis [Demo Fixture]**  
  *Claim*: Dedicated vector search engines achieve up to 5x lower query latency at scale (>2M vectors) compared to untuned pgvector collections.  
  *URL*: `https://github.com/pgvector/pgvector`  
  *Confidence*: 0.88 | *Status*: `verified`

---

## 7. Validation Center Audit

```json
{
  "status": "passed",
  "is_valid": true,
  "score": 0.96,
  "evidence_coverage": 0.94,
  "constraint_coverage": 1.0,
  "calculation_validity": 1.0,
  "missing_items": [],
  "warnings": [],
  "checks": [
    {
      "name": "Evidence Coverage",
      "passed": true,
      "notes": "Primary technical claims backed by verified documentation evidence (EV-001, EV-002, EV-003, EV-004) at 94% coverage; remaining items bounded by stated assumptions."
    },
    {
      "name": "Evidence Integrity",
      "passed": true,
      "notes": "All referenced evidence IDs exist in Evidence Ledger; zero dangling references."
    },
    {
      "name": "Constraint Coverage",
      "passed": true,
      "notes": "Privacy (isolated VPC), scale (100k PDFs), concurrency (20 users modeled), and budget fully addressed."
    },
    {
      "name": "Calculation Validity",
      "passed": true,
      "notes": "Deterministic calculations for vector RAM, disk storage estimates, and QPS throughput model verified."
    },
    {
      "name": "Required Sections",
      "passed": true,
      "notes": "All 15 required engineering report sections present."
    }
  ]
}
```

---

## 8. Decision Ledger

### [DEC-001] Vector Storage Engine
- **Recommendation**: Deploy self-hosted Qdrant with int8 scalar quantization on a single memory-optimized node inside private VPC.
- **Supporting Evidence**: `EV-001`, `EV-004`
- **Constraints Addressed**: Strict privacy, constrained budget (<$600/mo), 100k PDFs scale (2.5M vectors).
- **Trade-off**: Requires container operational management vs. SaaS, but eliminates egress fees and provides sub-20ms search latency.
- **Confidence**: `0.95`

### [DEC-002] Inference Hosting & Data Privacy
- **Recommendation**: Host quantized open-weights models (BAAI/bge-m3 and Llama-3.1-8B-Instruct 4-bit AWQ) on an isolated GPU instance using vLLM.
- **Supporting Evidence**: `EV-002`, `EV-003`
- **Constraints Addressed**: Strict privacy, 20 concurrent users, zero third-party data transmission.
- **Trade-off**: Fixed compute cost (~$410/mo) vs. serverless pay-per-token API charges, but completely bounds monthly spend.
- **Confidence**: `0.92`

---

## 9. Recommended Architecture & Alternatives

### Recommended: Self-Hosted Private VPC RAG (Qdrant + vLLM)
- **Ingestion**: Asynchronous chunking workers parsing PDFs into structured text chunks.
- **Vector DB**: Qdrant single-node with int8 scalar quantization (3.58 GB RAM vector index).
- **Embeddings**: Containerized Text Embeddings Inference (TEI) serving BAAI/bge-m3 on GPU.
- **Generation**: vLLM serving Llama-3.1-8B-Instruct AWQ on 1x NVIDIA A10G (24 GB VRAM).
- **Network**: Strict private VPC boundary, zero public internet egress, IAM role isolation.

### Alternative A: Self-Hosted PostgreSQL with pgvector
- **Pros**: Unified relational and vector storage in single ACID database; zero new primitives.
- **Cons**: pgvector HNSW index requires ~1.5x more memory than dedicated vector engines; WAL replication overhead during 100k PDF batch re-indexing.

### Alternative B: Cloud-Managed Enterprise (AWS OpenSearch + Bedrock PrivateLink)
- **Pros**: Zero cluster operational overhead; elastic auto-scaling.
- **Cons**: High baseline OCUs cost $350-$700/mo minimum when idle; token fees scale aggressively under sustained query volume, exceeding the $600/month budget.

---

## 10. Architecture Comparison Matrix

| Dimension | Recommended (Qdrant + vLLM) | Alternative A (pgvector) | Alternative B (Cloud-Managed) |
| :--- | :--- | :--- | :--- |
| **Data Privacy & Isolation** | 100% isolated private VPC; zero data egress | 100% isolated private VPC; ACID compliance | PrivateLink VPC endpoint, vendor multitenant host |
| **Estimated Monthly Cost** | ~$380 - $490/mo (Fixed EC2/GPU) | ~$320 - $440/mo (Fixed compute) | ~$950 - $1,400/mo (OCUs + token fees) |
| **Vector Query Latency (p99)** | ~18ms retrieval + ~220ms TTFT | ~45ms retrieval + ~220ms TTFT | ~65ms retrieval + ~450ms TTFT |
| **Operational Maintenance** | Low (Containerized, Docker Compose) | Medium (Vacuuming, index rebuilds) | Very Low (Fully managed serverless) |
| **Throughput Capacity** | Modeled for 20 users (up to 35 QPS) | Modeled for 20 users (up to 15 QPS) | Elastic auto-scaled |

---

## 11. Trade-offs

1. **TRADE-OFF**: Self-hosting Qdrant and vLLM eliminates unpredictable token billing and guarantees strict data privacy, in exchange for engineering ownership of container patching and monitoring.
2. **TRADE-OFF**: Int8 scalar quantization trades 0.5% vector recall precision for a 75% reduction in RAM (saving ~$180/mo on instance memory sizing).
3. **TRADE-OFF**: Chunking at 1000 tokens preserves rich semantic context for complex PDFs but increases embedding generation latency by ~15% during initial batch ingestion.

---

## 12. Implementation Roadmap

- **Phase 1: Ingestion & Vector Indexing (Weeks 1-2)**: Deploy Qdrant in VPC; run distributed chunking pipeline for 100k PDFs; validate int8 quantization recall and index memory footprint (<10 GB).
- **Phase 2: Inference & Hybrid Retrieval (Weeks 3-4)**: Deploy vLLM and TEI on GPU instance; configure hybrid search (dense + BM25 sparse); run concurrency simulation with 20 active users.
- **Phase 3: Security Hardening & Guardrails (Weeks 5-6)**: Enforce VPC endpoints and IAM boundaries; implement prompt injection defense; set up Prometheus/Grafana telemetry.
- **Phase 4: Production Rollout & User Acceptance (Weeks 7-8)**: Pilot with 20 concurrent enterprise users; measure p95 latency (<1.5s SLA); finalize operational runbooks and S3 vector snapshots.
