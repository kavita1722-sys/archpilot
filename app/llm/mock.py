"""Deterministic, domain-aware mock LLM provider for reliable testing and demos."""

import json
import re
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from app.core.logging import logger
from app.llm.base import LLMProvider
from app.schemas.decision import DecisionItem
from app.schemas.evidence import EvidenceFilterResult, EvidenceItem
from app.schemas.plan import Plan, PlanStep, StepStatus
from app.schemas.result import FinalResult, ValidationResult
from app.schemas.task import NormalizedTask

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Offline, deterministic mock LLM provider generating simulated fixtures for offline testing, demos, and canonical scenarios."""

    async def generate_text(
        self, prompt: str, system: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        """Generate deterministic text matching system engineering prompts."""
        logger.debug("MockLLMProvider generate_text called with prompt preview: %s", prompt[:80])
        return (
            "ArchPilot Engineering Synthesis [Demo / Mock Mode]: Based on deterministic capacity calculations "
            "and architectural boundary constraints, the primary bottleneck is write throughput. "
            "Horizontal partitioning and tiering to distributed object storage is recommended."
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Return high-fidelity structured Pydantic objects tailored to engineering contexts."""
        logger.debug(
            "MockLLMProvider generate_structured called for schema: %s", schema.__name__
        )

        prompt_lower = prompt.lower()
        is_rag_task = bool(
            re.search(r"\brag\b", prompt_lower)
            or "pdf" in prompt_lower
            or "100,000" in prompt_lower
            or "100000" in prompt_lower
            or "qdrant" in prompt_lower
        )

        # 1. NormalizedTask
        if issubclass(schema, NormalizedTask):
            if is_rag_task:
                return schema(
                    normalized_task="Design a production-ready RAG architecture for 100,000 PDF documents, 20 concurrent users, strict data privacy, and a constrained monthly infrastructure budget.",
                    domain="Enterprise Search & Retrieval-Augmented Generation (RAG)",
                    extracted_constraints={
                        "document_volume": "100,000 PDF documents",
                        "concurrency": "20 concurrent users",
                        "privacy": "Strict data privacy (no third-party training, isolated VPC)",
                        "budget": "Constrained monthly infrastructure budget (<$600/month)",
                        "comparison_required": "Compare two viable architectures",
                        "calculation_required": True,
                    },
                    target_metric="Vector Index RAM (GB), Persistent Disk (GB), Query Throughput (QPS), Monthly Cost ($)",
                    requires_calculation=True,
                    key_variables=[
                        "100,000 PDF documents",
                        "25 chunks per PDF (2.5M vectors)",
                        "1536-dimensional embeddings",
                        "20 concurrent user query sessions",
                        "Sub-1.5s p95 latency SLA",
                    ],
                )

            domain = "Distributed Storage & Capacity Planning"
            metric = "Required Storage & Bandwidth"
            requires_calc = True
            key_vars = ["Daily Active Users", "Item Size", "Retention Period", "Peak Ratio"]

            if "cache" in prompt_lower or "memory" in prompt_lower or "redis" in prompt_lower:
                domain = "In-Memory Caching & Latency Architecture"
                metric = "RAM Capacity (GB) & Cache Hit Ratio"
                key_vars = ["Read QPS", "Working Set Size", "TTL", "Object Size"]
            elif "database" in prompt_lower or "qps" in prompt_lower or "shard" in prompt_lower:
                domain = "Database Scaling & Partitioning"
                metric = "IOPS & Shard Count"
                key_vars = ["Write QPS", "Row Size", "IOPS Per Node", "Replication Factor"]

            return schema(
                normalized_task=prompt.strip().split("\n")[0][:250],
                domain=domain,
                extracted_constraints={
                    "concurrency_target": "High Concurrency",
                    "availability_target": "99.99%",
                    "calculation_required": True,
                },
                target_metric=metric,
                requires_calculation=requires_calc,
                key_variables=key_vars,
            )

        # 2. Plan
        if issubclass(schema, Plan):
            if is_rag_task:
                steps = [
                    PlanStep(
                        id=1,
                        objective="Research vector database memory footprint and scalar quantization benchmarks.",
                        tool="web_search",
                        inputs={"query": "qdrant memory requirements 1536 dimension vector index scalar quantization", "max_results": 4},
                        success_criteria="Empirical memory scaling and quantization benchmarks retrieved.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=2,
                        objective="Calculate raw vector index RAM requirements for 100k PDFs (2.5M 1536-dim vectors in float32).",
                        tool="calculator",
                        inputs={"expression": "100000 * 25 * 1536 * 4 / (1024 * 1024 * 1024)"},
                        success_criteria="Total raw vector RAM in GB calculated deterministically.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=3,
                        objective="Fetch official Qdrant scalar quantization technical documentation for empirical compression ratio.",
                        tool="url_fetch",
                        inputs={"url": "https://qdrant.tech/documentation/guides/quantization/"},
                        success_criteria="Verified scalar quantization memory reduction ratio and recall metrics.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=4,
                        objective="Calculate quantized vector index memory with int8 scalar quantization (4x compression).",
                        tool="calculator",
                        inputs={"expression": "14.305 / 4"},
                        success_criteria="Quantized RAM requirement in GB calculated.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=5,
                        objective="Calculate theoretical interactive query throughput (QPS) for 20 concurrent users assuming 2 queries/min per user.",
                        tool="calculator",
                        inputs={"expression": "(20 * 2) / 60"},
                        success_criteria="Theoretical peak and average query throughput QPS determined based on stated concurrency assumptions.",
                        status=StepStatus.PENDING,
                    ),
                ]
                goal = "Design and capacity-plan an evidence-backed private RAG architecture for 100,000 PDFs and 20 concurrent users."
                assumptions = [
                    "ASSUMPTION: 100,000 PDFs average 25 chunks each (total 2.5 million chunks).",
                    "ASSUMPTION: Embeddings use 1536 dimensions (float32 = 4 bytes per dim).",
                    "ASSUMPTION: Int8 scalar quantization reduces RAM by 4x with <0.5% recall penalty.",
                    "ASSUMPTION: 20 concurrent users generate 2 queries/min each (0.67 QPS avg, 2.0 QPS peak throughput model; theoretical capacity sizing, not an executed empirical benchmark).",
                ]
                return schema(goal=goal, assumptions=assumptions, steps=steps)

            elif "cache" in prompt_lower:
                steps = [
                    PlanStep(
                        id=1,
                        objective="Calculate total daily raw working set data volume in gigabytes.",
                        tool="calculator",
                        inputs={"expression": "500000 * 86400 * 2048 / (1024 * 1024 * 1024)"},
                        success_criteria="Raw daily data volume in GB determined.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=2,
                        objective="Apply 20% Pareto working set rule with 25% memory overhead factor.",
                        tool="calculator",
                        inputs={"expression": "82397 * 0.20 * 1.25"},
                        success_criteria="Target active cache cluster memory capacity in GB.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=3,
                        objective="Determine required Redis/Memcached cluster nodes assuming 64GB nodes.",
                        tool="calculator",
                        inputs={"expression": "ceil(20599 / 64)"},
                        success_criteria="Recommended minimum node cluster count determined.",
                        status=StepStatus.PENDING,
                    ),
                ]
                goal = "Determine cache cluster memory sizing and node provisioning."
                assumptions = [
                    "80/20 rule: 20% of content generates 80% of read traffic",
                    "Average cached payload size is 2 KB",
                    "Redis memory allocator overhead estimated at 25%",
                ]
                return schema(goal=goal, assumptions=assumptions, steps=steps)
            else:
                steps = [
                    PlanStep(
                        id=1,
                        objective="Calculate raw daily payload ingestion volume in terabytes.",
                        tool="calculator",
                        inputs={"expression": "10000000 * 3 * 500000 / (1024 * 1024 * 1024 * 1024)"},
                        success_criteria="Daily raw ingestion volume in TB calculated.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=2,
                        objective="Calculate 1-year persistent storage with 3x replication factor.",
                        tool="calculator",
                        inputs={"expression": "13.64 * 365 * 3"},
                        success_criteria="Annual replicated storage capacity in TB determined.",
                        status=StepStatus.PENDING,
                    ),
                    PlanStep(
                        id=3,
                        objective="Calculate peak ingress bandwidth in Gigabits per second (Gbps) assuming 3x peak burst.",
                        tool="calculator",
                        inputs={"expression": "(13.64 * 1024 * 8 / 86400) * 3"},
                        success_criteria="Peak ingress network bandwidth in Gbps.",
                        status=StepStatus.PENDING,
                    ),
                ]
                goal = "System capacity planning: storage volume, replication overhead, and network bandwidth."
                assumptions = [
                    "Daily active write volume modeled under steady state",
                    "Triple replication for fault tolerance across failure domains",
                    "Peak traffic ratio estimated at 3.0x average daily ingestion",
                ]
                return schema(goal=goal, assumptions=assumptions, steps=steps)

        # 3. EvidenceItem
        if issubclass(schema, EvidenceItem):
            return schema(
                id="EV-001",
                title="Qdrant Scalar Quantization Technical Benchmarks",
                url="https://qdrant.tech/documentation/guides/quantization/",
                source_type="documentation",
                claim="Scalar quantization (int8) compresses 1536-dim vector memory by 4x with less than 0.5% recall loss.",
                excerpt="Quantization maps float32 to int8, reducing RAM footprint by 75% while maintaining 99.4% search accuracy on standard benchmarks.",
                relevance=0.96,
                confidence=0.94,
                status="verified",
            )

        # 4. EvidenceFilterResult
        if issubclass(schema, EvidenceFilterResult):
            return schema(
                evaluation="supporting",
                confidence=0.94,
                reasoning="The excerpt provides authoritative benchmarks directly verifying the vector quantization compression factor and memory sizing.",
            )

        # 5. DecisionItem
        if issubclass(schema, DecisionItem):
            return schema(
                id="DEC-001",
                question="Which vector storage engine satisfies strict privacy and constrained budget for 100k PDFs?",
                recommendation="Deploy self-hosted Qdrant with int8 scalar quantization on an AWS EC2 m6i.xlarge instance inside an isolated private VPC.",
                supporting_evidence_ids=["EV-001", "EV-002"],
                constraints_addressed=["strict privacy", "constrained budget", "100,000 PDFs scale"],
                tradeoffs=[
                    "Requires container lifecycle management vs SaaS, but eliminates per-token API egress costs and ensures zero third-party data leakage.",
                    "Int8 quantization trades 0.5% vector recall precision for a 75% reduction in RAM footprint.",
                ],
                assumptions=[
                    "2.5M vectors fit in under 10 GB of RAM with int8 quantization",
                    "Single-node Qdrant comfortably handles up to 35 QPS at this scale",
                ],
                confidence=0.95,
            )

        # 6. ValidationResult
        if issubclass(schema, ValidationResult):
            return schema(
                status="passed",
                is_valid=True,
                score=0.96,
                evidence_coverage=0.94,
                constraint_coverage=1.0,
                calculation_validity=1.0,
                missing_items=[],
                warnings=[],
                checks=[
                    {"name": "Evidence Coverage", "passed": True, "notes": "Primary technical claims backed by verified documentation evidence (EV-001, EV-002, EV-003) at 94% coverage; remaining items bounded by stated assumptions."},
                    {"name": "Evidence Integrity", "passed": True, "notes": "All referenced evidence IDs exist in Evidence Ledger; zero dangling references."},
                    {"name": "Constraint Coverage", "passed": True, "notes": "Privacy (isolated VPC), scale (100k PDFs), concurrency (20 users modeled), and budget fully addressed."},
                    {"name": "Calculation Validity", "passed": True, "notes": "Deterministic calculations for vector RAM, disk storage estimates, and QPS throughput model verified."},
                    {"name": "Required Sections", "passed": True, "notes": "All 15 required engineering report sections present."},
                ],
                research_needed=None,
                feedback=None,
            )

        # 7. FinalResult
        if issubclass(schema, FinalResult):
            if is_rag_task:
                return schema(
                    executive_summary=(
                        "[Mock LLM Mode / Simulated Scenario]: A self-hosted, private VPC architecture "
                        "coupling Qdrant (with int8 scalar quantization) and vLLM (serving quantized open-weights models) "
                        "optimally resolves the 100,000 PDF RAG requirement. This topology satisfies strict data privacy "
                        "with zero external data egress, is capacity-modeled to sustain 20 concurrent users at sub-300ms retrieval latency, "
                        "and bounds estimated monthly cloud spend to ~$410/month based on stated pricing assumptions—slashing "
                        "projected costs by 65% compared to commercial managed alternatives. "
                        "(Note: Generated under LLM_PROVIDER=mock using simulated benchmark fixtures and sizing models; not a live empirical benchmark)."
                    ),
                    problem_definition=(
                        "Design a production-ready RAG system ingesting 100,000 PDF documents (~2.5M chunks) supporting "
                        "20 concurrent analytical users under strict privacy requirements (zero external training or data egress) "
                        "and a constrained infrastructure budget."
                    ),
                    requirements=[
                        "Ingest and index 100,000 PDFs with average 25 chunks/doc (2.5 million vectors)",
                        "Model and support 20 concurrent users with target interactive query latency < 1.5s (p95)",
                        "Strict data privacy: zero transmission to external SaaS LLM APIs or public endpoints",
                        "Constrained budget: monthly infrastructure target under $600/month",
                        "Deterministic capacity validation for RAM, NVMe disk, and inference throughput",
                    ],
                    assumptions=[
                        "ASSUMPTION: 100,000 PDFs average 20-30 pages, yielding ~25 text chunks of 1000 tokens each (~2.5 million total vectors).",
                        "ASSUMPTION: Embedding model uses 1536 dimensions (e.g. BAAI/bge-m3 or text-embedding-3-small compatible).",
                        "ASSUMPTION: Float32 representation requires 4 bytes per dimension (6 KB raw vector).",
                        "ASSUMPTION: 20 concurrent users generate on average 2 queries/minute each = 0.67 QPS average, with peak burst multiplier of 3.0x = 2.0 QPS (theoretical capacity model, not live load test).",
                        "ASSUMPTION: Int8 scalar quantization reduces vector memory footprint by 75% with <0.5% recall penalty.",
                    ],
                    recommended_architecture={
                        "name": "Self-Hosted Private VPC RAG (Qdrant + vLLM / Ollama)",
                        "description": "Fully air-gapped or private VPC deployment with Qdrant vector engine and self-hosted quantized LLM/embedding inference.",
                        "components": {
                            "ingestion_pipeline": "Async Ray/Celery workers parsing PDFs into structured Markdown chunks",
                            "vector_database": "Qdrant (single-node with int8 scalar quantization, HNSW in-memory index, payload on disk)",
                            "embedding_inference": "Self-hosted TEI (Text Embeddings Inference) serving BAAI/bge-m3 on 1x NVIDIA T4 GPU",
                            "generation_inference": "vLLM serving Llama-3.1-8B-Instruct AWQ (4-bit) on 1x NVIDIA A10G/L4 GPU",
                            "orchestration_api": "FastAPI asynchronous service with semantic caching and hybrid search reranker",
                            "network_security": "Strict VPC boundary, no public internet egress, IAM role isolation, TLS encryption at rest and in transit",
                        },
                    },
                    alternative_architecture_a={
                        "name": "Self-Hosted Hybrid PostgreSQL (pgvector + Containerized TEI)",
                        "description": "Relational PostgreSQL database leveraging pgvector extension and local containerized embedding service.",
                        "pros": ["Unified relational and vector storage in single ACID database", "Zero new infrastructure primitives if Postgres already in stack"],
                        "cons": ["pgvector HNSW index requires ~1.5x more memory than dedicated vector engines", "Vacuuming and WAL replication overhead during bulk 100k PDF batch re-indexing"],
                    },
                    alternative_architecture_b={
                        "name": "Cloud-Managed Enterprise VPC (AWS OpenSearch Serverless + AWS Bedrock PrivateLink)",
                        "description": "Fully managed cloud serverless vector search and foundation models accessed exclusively via AWS PrivateLink VPC endpoints.",
                        "pros": ["Zero cluster operational overhead", "Elastic auto-scaling from zero"],
                        "cons": ["High baseline OCUs cost ~$350-$700/mo minimum even when idle", "Per-token Bedrock inference charges scale aggressively under sustained query volume"],
                    },
                    architecture_comparison=[
                        {"dimension": "Data Privacy & Isolation", "recommended": "100% isolated private VPC; zero data egress", "alt_a_pgvector": "100% isolated private VPC; ACID compliance", "alt_b_cloud_managed": "PrivateLink VPC endpoint, SOC2 compliant, vendor shared multitenant host"},
                        {"dimension": "Monthly Operating Cost", "recommended": "~$380 - $490/month (Fixed EC2/GPU instances)", "alt_a_pgvector": "~$320 - $440/month (Fixed compute)", "alt_b_cloud_managed": "~$950 - $1,400/month (OCUs + Bedrock token fees)"},
                        {"dimension": "Vector Query Latency (p99)", "recommended": "18ms retrieval + 220ms TTFT", "alt_a_pgvector": "45ms retrieval + 220ms TTFT", "alt_b_cloud_managed": "65ms retrieval + 450ms TTFT"},
                        {"dimension": "Operational Maintenance", "recommended": "Low (Docker containerized, auto-healing)", "alt_a_pgvector": "Medium (Vacuuming, index re-builds)", "alt_b_cloud_managed": "Very Low (Serverless AWS managed)"},
                        {"dimension": "Throughput Capacity", "recommended": "Up to 35 QPS (Comfortably exceeds 2 QPS peak)", "alt_a_pgvector": "Up to 15 QPS", "alt_b_cloud_managed": "Elastic auto-scaled"},
                    ],
                    capacity_calculations=[
                        {"metric": "Total Vector Count", "formula": "100,000 PDFs * 25 chunks/PDF", "result": 2500000, "unit": "chunks (estimated from chunking assumption)"},
                        {"metric": "Raw Vector Memory (Float32)", "formula": "2,500,000 * 1536 * 4 bytes / (1024^3)", "result": 14.31, "unit": "GB"},
                        {"metric": "Quantized Vector Memory (Int8)", "formula": "14.31 GB / 4", "result": 3.58, "unit": "GB"},
                        {"metric": "Estimated Total Working Set RAM (with HNSW index & OS buffer)", "formula": "3.58 GB * 1.5 + 4 GB OS headroom", "result": 9.37, "unit": "GB (estimate)"},
                        {"metric": "Estimated Persistent Chunk Text Disk Storage", "formula": "2,500,000 * 1000 chars * ~4 bytes/char (including metadata overhead) / (1024^3)", "result": 9.31, "unit": "GB (estimate)"},
                        {"metric": "Estimated Average & Peak Query Throughput", "formula": "(20 users * 2 queries/min) / 60 = 0.67 QPS; Peak (3x) = 2.0 QPS (theoretical throughput model)", "result": 2.0, "unit": "QPS (estimate)"},
                        {"metric": "Estimated Monthly Cloud Infrastructure Cost", "formula": "EC2 g5.xlarge (1x A10G 24GB VRAM) @ $1.006/hr * 730 hrs = ~$734/mo (On-Demand estimate) or ~$410/mo (1-yr Savings Plan estimate based on stated AWS pricing assumptions)", "result": 410.0, "unit": "$/month (estimate)"},
                    ],
                    evidence=[
                        EvidenceItem(
                            id="EV-001",
                            title="Qdrant Scalar Quantization & Memory Documentation [Demo Fixture]",
                            url="https://qdrant.tech/documentation/guides/quantization/",
                            source_type="documentation",
                            claim="Scalar quantization (int8) compresses 1536-dim vectors by 4x (from 14.3 GB to 3.58 GB) with <0.5% recall loss according to published vendor documentation.",
                            excerpt="Quantization maps float32 to int8, reducing RAM footprint by 75% while maintaining 99.4% search accuracy on standard benchmarks (published vendor documentation).",
                            relevance=0.96,
                            confidence=0.94,
                            status="verified",
                        ),
                        EvidenceItem(
                            id="EV-002",
                            title="vLLM PagedAttention High-Throughput Inference Engine [Demo Fixture]",
                            url="https://docs.vllm.ai/en/latest/",
                            source_type="documentation",
                            claim="PagedAttention achieves 2-4x higher throughput than HuggingFace TGI on 24GB GPUs according to published vLLM documentation, providing capacity for up to 20 concurrent user sessions.",
                            excerpt="vLLM enables continuous batching and virtual memory management for LLM key-value caches, handling dozens of concurrent requests without OOM (published vendor documentation).",
                            relevance=0.94,
                            confidence=0.91,
                            status="verified",
                        ),
                        EvidenceItem(
                            id="EV-003",
                            title="AWS PrivateLink & VPC Endpoint Security Architecture [Demo Fixture]",
                            url="https://docs.aws.amazon.com/whitepapers/latest/aws-privatelink/aws-privatelink.html",
                            source_type="documentation",
                            claim="Deploying inference inside dedicated VPC with PrivateLink ensures traffic never traverses the public internet, satisfying strict compliance.",
                            excerpt="AWS PrivateLink provides private connectivity between VPCs, supported AWS services, and on-premises networks without exposing traffic to the public internet.",
                            relevance=0.92,
                            confidence=0.95,
                            status="verified",
                        ),
                        EvidenceItem(
                            id="EV-004",
                            title="pgvector vs Dedicated Vector Search Scaling Analysis [Demo Fixture]",
                            url="https://github.com/pgvector/pgvector",
                            source_type="benchmark",
                            claim="Dedicated vector search engines achieve up to 5x lower query latency at scale (>2M vectors) compared to pgvector without HNSW tuning according to published community benchmarks.",
                            excerpt="While pgvector is convenient, dedicated vector databases like Qdrant provide superior memory efficiency and filtering latency on multi-million vector collections.",
                            relevance=0.89,
                            confidence=0.88,
                            status="verified",
                        ),
                    ],
                    decisions=[
                        DecisionItem(
                            id="DEC-001",
                            question="Which vector storage engine should be selected for 2.5M vectors under strict budget and privacy?",
                            recommendation="Deploy self-hosted Qdrant with int8 scalar quantization on a single memory-optimized node inside private VPC.",
                            supporting_evidence_ids=["EV-001", "EV-004"],
                            constraints_addressed=["strict privacy", "constrained budget", "100,000 PDFs scale"],
                            tradeoffs=["Requires container lifecycle management vs SaaS, but eliminates egress costs and provides sub-20ms search latency."],
                            assumptions=["2.5M vectors fit in under 10 GB of RAM with int8 quantization"],
                            confidence=0.95,
                        ),
                        DecisionItem(
                            id="DEC-002",
                            question="How should LLM generation and embedding inference be hosted to meet data privacy?",
                            recommendation="Host quantized open-weights models (BAAI/bge-m3 and Llama-3.1-8B-Instruct 4-bit AWQ) on an isolated GPU instance using vLLM.",
                            supporting_evidence_ids=["EV-002", "EV-003"],
                            constraints_addressed=["strict privacy", "20 concurrent users", "zero third-party training"],
                            tradeoffs=["Requires 1x 24GB VRAM GPU instance ($410/mo) vs serverless pay-per-token, but caps monthly spend predictably regardless of token volume."],
                            assumptions=["Llama-3.1-8B quantized fits in 8 GB VRAM, leaving 16 GB for KV cache to theoretically support 20 concurrent users"],
                            confidence=0.92,
                        ),
                    ],
                    trade_offs=[
                        "TRADE-OFF: Self-hosting Qdrant and vLLM eliminates unpredictable token billing and guarantees strict data privacy, in exchange for engineering ownership of container patching and monitoring.",
                        "TRADE-OFF: Int8 scalar quantization trades 0.5% vector recall precision for a 75% reduction in RAM (saving ~$180/mo on memory instance sizing).",
                        "TRADE-OFF: Chunking at 1000 tokens preserves rich semantic context for complex PDFs but increases embedding generation latency by ~15% during initial batch ingestion.",
                    ],
                    risks=[
                        {"risk": "GPU Out-Of-Memory during concurrent generation spikes", "impact": "High", "mitigation": "Configure vLLM max-num-seqs=24 and enable dynamic request queueing with HTTP 429 backpressure."},
                        {"risk": "PDF ingestion backlog on 100,000 documents", "impact": "Medium", "mitigation": "Run batch ingestion pipeline as distributed spot EC2 workers, processing 100k PDFs in ~3 hours at one-time cost of ~$12."},
                        {"risk": "Model drift or hallucination on technical domain PDFs", "impact": "Medium", "mitigation": "Implement reciprocal rank fusion (RRF) with hybrid sparse BM25 + dense vector search and strict citation prompt templates."},
                    ],
                    implementation_roadmap=[
                        {"phase": "Phase 1: Ingestion & Vector Indexing (Weeks 1-2)", "deliverables": ["Deploy Qdrant in VPC", "Run distributed chunking & embedding pipeline for 100k PDFs", "Validate int8 quantization recall and index memory footprint (<10 GB)"]},
                        {"phase": "Phase 2: Inference & Hybrid Retrieval (Weeks 3-4)", "deliverables": ["Deploy vLLM and TEI on GPU instance", "Wire hybrid search (Qdrant dense + BM25 sparse) with reranking", "Run concurrency benchmark simulating 20 active users"]},
                        {"phase": "Phase 3: Security Hardening & Guardrails (Weeks 5-6)", "deliverables": ["Enforce VPC endpoints and IAM role boundaries", "Implement prompt injection input filters and citation ground-truth validation", "Setup Prometheus / Grafana telemetry for QPS, latency, and VRAM"]},
                        {"phase": "Phase 4: Production Rollout & User Acceptance (Weeks 7-8)", "deliverables": ["Pilot with 20 concurrent enterprise users", "Measure query latency SLAs (p95 < 1.5s)", "Finalize operational runbook and automated daily vector snapshots to S3"]},
                    ],
                    confidence=0.94,
                    evidence_coverage=0.95,
                    plan_summary="Executed structured 5-phase capacity and architectural modeling (Mock mode): documentation research, theoretical vector RAM calculation, documentation verification, quantization sizing, and theoretical QPS throughput modeling.",
                    actions_taken=[
                        {"step": 1, "tool": "web_search", "outcome": "Retrieved vector DB memory benchmarks."},
                        {"step": 2, "tool": "calculator", "outcome": "Raw vector RAM calculated at 14.31 GB."},
                        {"step": 3, "tool": "url_fetch", "outcome": "Verified Qdrant int8 quantization 4x compression ratio."},
                        {"step": 4, "tool": "calculator", "outcome": "Quantized RAM requirement determined at 3.58 GB."},
                        {"step": 5, "tool": "calculator", "outcome": "Peak user query throughput theoretically modeled at 2.0 QPS based on concurrency assumptions."},
                    ],
                    observations=[
                        "100,000 PDFs yield ~2.5 million vectors (1536-dim), requiring 14.31 GB raw float32 memory.",
                        "Scalar quantization reduces vector RAM to 3.58 GB, enabling a single modest instance to host the index.",
                        "20 concurrent users modeled at 0.67 QPS average and 2.0 QPS peak based on stated query frequency assumptions, within single GPU/vLLM capacity.",
                    ],
                    calculations=[
                        {"metric": "Raw Vector Memory", "formula": "100000 * 25 * 1536 * 4 / (1024^3)", "result": 14.31, "unit": "GB"},
                        {"metric": "Quantized Vector Memory", "formula": "14.305 / 4", "result": 3.58, "unit": "GB"},
                        {"metric": "Estimated Query Throughput", "formula": "(20 * 2) / 60", "result": 0.67, "unit": "QPS (avg estimate)"},
                        {"metric": "Estimated Peak Throughput", "formula": "0.67 * 3.0", "result": 2.0, "unit": "QPS (peak estimate)"},
                    ],
                    final_answer=(
                        "### Final Engineering Decision: Self-Hosted Private VPC RAG Architecture (Simulated Mock Fixture)\n\n"
                        "> **Execution Mode Notice**: Generated under `LLM_PROVIDER=mock`. Findings and sizing figures represent deterministic capacity modeling and simulated documentation fixtures, not a live empirical load test.\n\n"
                        "1. **Vector Indexing & Storage**:\n"
                        "   - Single-node Qdrant instance with int8 scalar quantization (`3.58 GB` vector index).\n"
                        "   - Full dataset fits comfortably in 16 GB RAM with OS buffer and HNSW cache.\n\n"
                        "2. **Inference & Privacy**:\n"
                        "   - vLLM serving Llama-3.1-8B-Instruct AWQ (4-bit) on 1x NVIDIA A10G (24 GB VRAM).\n"
                        "   - 100% private VPC network isolation; zero data egress to public endpoints.\n\n"
                        "3. **Capacity & Cost**:\n"
                        "   - Sized to sustain 20 concurrent users (2.0 peak QPS theoretical estimate) at sub-300ms retrieval latency based on capacity modeling.\n"
                        "   - Monthly infrastructure estimated at ~$410/month on 1-year savings plan based on AWS pricing assumptions."
                    ),
                    decision_trace=[
                        {
                            "decision": "Self-hosted Qdrant with Int8 Scalar Quantization",
                            "constraint": "Constrained budget & 100k PDFs scale",
                            "evidence": "EV-001 (Qdrant quantization guide)",
                            "calculation": "14.31 GB / 4 = 3.58 GB RAM",
                            "trade_off": "0.5% recall penalty vs 75% memory reduction",
                        },
                        {
                            "decision": "vLLM Inference on Dedicated Private VPC GPU",
                            "constraint": "Strict data privacy & 20 concurrent users",
                            "evidence": "EV-002 (vLLM PagedAttention documentation)",
                            "calculation": "20 users * 2 QPM = 2.0 QPS peak throughput (theoretical estimate based on stated user query rate)",
                            "trade_off": "Fixed GPU instance cost vs serverless pay-per-token API charges",
                        },
                    ],
                )

            # Default generic capacity response
            return schema(
                executive_summary=(
                    "[Mock LLM Mode / Simulated Scenario]: Architecture sizing and capacity constraints "
                    "have been evaluated using deterministic mathematical modeling based on stated baseline assumptions. "
                    "A distributed tiering strategy with horizontal sharding is selected to ensure "
                    "p99 latency compliance within budget boundaries."
                ),
                problem_definition="High-throughput distributed data ingestion and retention sizing under strict availability SLAs.",
                requirements=["Scale across multi-region deployment", "Meet sub-200ms p99 latency SLA", "Ensure 99.999999999% durability"],
                assumptions=[
                    "ASSUMPTION: Daily active write volume modeled under steady state",
                    "ASSUMPTION: Triple replication for fault tolerance across failure domains",
                    "ASSUMPTION: Peak traffic ratio estimated at 3.0x average daily ingestion",
                ],
                recommended_architecture={"tiering": "NVMe Hot Buffer -> Distributed Object Storage Cold Tier"},
                alternative_architecture_a={"name": "All-SSD Distributed SAN Cluster"},
                alternative_architecture_b={"name": "Cloud-Native Serverless DynamoDB"},
                architecture_comparison=[
                    {"dimension": "Annual Cost", "recommended": "$42,000", "alt_a": "$115,000", "alt_b": "$88,000"},
                    {"dimension": "Ingress Latency", "recommended": "15ms", "alt_a": "5ms", "alt_b": "25ms"},
                ],
                capacity_calculations=[
                    {"metric": "Estimated Daily Volume", "formula": "10000000 * 3 * 500000 / (1024^4)", "result": 13.64, "unit": "TB/day (estimate based on assumed item size)"},
                    {"metric": "Estimated Annual Replicated Storage", "formula": "13.64 * 365 * 3", "result": 14935.8, "unit": "TB/year (estimate based on 3x replication assumption)"},
                    {"metric": "Estimated Peak Ingress Bandwidth", "formula": "(13.64 * 1024 * 8 / 86400) * 3", "result": 3.88, "unit": "Gbps (estimate based on 3x peak multiplier assumption)"},
                ],
                evidence=[
                    EvidenceItem(
                        id="EV-001",
                        title="High-Throughput Storage Tiering Documentation [Demo Fixture]",
                        url="https://docs.aws.amazon.com/s3/",
                        source_type="documentation",
                        claim="Object storage lifecycle tiering yields 78% cost reduction after 7 days.",
                        excerpt="Lifecycle policies transition data from standard storage to infrequent access.",
                        relevance=0.92,
                        confidence=0.89,
                        status="verified",
                    )
                ],
                decisions=[
                    DecisionItem(
                        id="DEC-001",
                        question="Which tiering model balances durability and storage expenditure?",
                        recommendation="Tier hot buffer data to cold object storage after 7 days.",
                        supporting_evidence_ids=["EV-001"],
                        constraints_addressed=["retention SLA", "budget cap"],
                        tradeoffs=["100ms retrieval latency for archived objects older than 7 days."],
                        assumptions=["90% of read queries target objects under 7 days old."],
                        confidence=0.91,
                    )
                ],
                trade_offs=[
                    "Triple replication increases storage expenditure by 200% but satisfies 99.999999999% durability SLA.",
                    "Tiering to object storage introduces 100ms retrieval latency for objects older than 7 days.",
                    "Hash sharding complicates global range queries, requiring secondary indexing.",
                ],
                risks=[
                    {"risk": "Peak ingress surge exceeding 3.88 Gbps", "impact": "High", "mitigation": "Dual 10 GbE interfaces with buffer queues"},
                ],
                implementation_roadmap=[
                    {"phase": "Phase 1: NVMe Ingestion Tier", "deliverables": ["Deploy 4x ingestion brokers"]},
                    {"phase": "Phase 2: Object Storage Tiering", "deliverables": ["Configure S3 lifecycle rules"]},
                ],
                confidence=0.92,
                evidence_coverage=0.91,
                plan_summary="Executed structured 3-phase capacity modeling: raw volume estimation, replication scaling, and peak ingress network bandwidth.",
                actions_taken=[
                    {"step": 1, "tool": "calculator", "outcome": "Daily ingestion computed."},
                    {"step": 2, "tool": "calculator", "outcome": "Annual storage with replication verified."},
                    {"step": 3, "tool": "calculator", "outcome": "Peak bandwidth modeled."},
                ],
                observations=[
                    "Raw daily ingestion requires ~13.64 TB/day.",
                    "Annual persistent retention with 3x replication requires ~14,935.8 TB (~14.9 PB).",
                    "Peak network ingress reaches ~3.88 Gbps during peak traffic bursts.",
                ],
                calculations=[
                    {"metric": "Estimated Daily Volume", "formula": "10000000 * 3 * 500000 / (1024^4)", "result": 13.64, "unit": "TB/day"},
                    {"metric": "Estimated Annual Replicated Storage", "formula": "13.64 * 365 * 3", "result": 14935.8, "unit": "TB/year"},
                    {"metric": "Estimated Peak Ingress Bandwidth", "formula": "(13.64 * 1024 * 8 / 86400) * 3", "result": 3.88, "unit": "Gbps"},
                ],
                final_answer=(
                    "### Architectural Decision: Tiered Storage & Distributed Ingestion Pipeline (Simulated Mock Fixture)\n\n"
                    "> **Notice**: Generated under `LLM_PROVIDER=mock` using deterministic sizing heuristics and reference documentation fixtures.\n\n"
                    "1. **Storage Tiering Architecture**:\n"
                    "   - Ingest into hot NVMe/SSD buffer partitioned across distributed brokers.\n"
                    "   - Tier out to cold object storage after 7 days, reducing cost by 78%.\n"
                    "   - Provision **15 PB** total raw cloud storage capacity for Year 1.\n\n"
                    "2. **Network & Ingress Bandwidth**:\n"
                    "   - Dual 10 Gbps redundant uplink switches to comfortably handle 3.88 Gbps peak bursts with headroom.\n\n"
                    "3. **Partitioning & Sharding**:\n"
                    "   - Shard by `user_id` hash across 32 logical partitions to distribute write IOPS evenly."
                ),
                decision_trace=[
                    {
                        "decision": "Provision 15 PB Annual Object Storage",
                        "constraint": "1-year retention SLA, 3x replication durability",
                        "evidence": "13.64 TB daily ingest * 365 days * 3 replicas = 14,935.8 TB (estimate based on stated sizing assumptions)",
                        "calculation": "13.64 * 365 * 3 = 14935.8",
                        "trade_off": "Higher initial cloud cost vs. guaranteed data resilience",
                    },
                ],
            )

        # Fallback for unexpected schema
        return schema()
