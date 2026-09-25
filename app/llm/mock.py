"""Deterministic, domain-aware mock LLM provider for reliable testing and demos."""

import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from app.core.logging import logger
from app.llm.base import LLMProvider
from app.schemas.plan import Plan, PlanStep, StepStatus
from app.schemas.result import FinalResult, ValidationResult
from app.schemas.task import NormalizedTask

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Offline, deterministic LLM provider tailored for system engineering benchmarks."""

    async def generate_text(
        self, prompt: str, system: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        """Generate deterministic text matching system engineering prompts."""
        logger.debug("MockLLMProvider generate_text called with prompt preview: %s", prompt[:80])
        return (
            "ArchPilot Engineering Synthesis: Based on deterministic capacity calculations "
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

        # 1. NormalizedTask
        if issubclass(schema, NormalizedTask):
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
            if "cache" in prompt_lower:
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
            else:
                # Default storage & capacity planning plan
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

            return schema(
                goal=goal,
                assumptions=assumptions,
                steps=steps,
            )

        # 3. ValidationResult
        if issubclass(schema, ValidationResult):
            return schema(
                is_valid=True,
                score=0.96,
                checks=[
                    {"name": "Mathematical Precision", "passed": True, "notes": "All equations verified deterministically via AST calculator."},
                    {"name": "Constraint Adherence", "passed": True, "notes": "Capacity thresholds accommodate peak multipliers."},
                    {"name": "Decision Traceability", "passed": True, "notes": "Every capacity recommendation directly maps to calculation evidence."},
                ],
                feedback=None,
            )

        # 4. FinalResult
        if issubclass(schema, FinalResult):
            return schema(
                executive_summary=(
                    "ArchPilot Engineering Decision: Architecture sizing and capacity constraints "
                    "have been verified using deterministic mathematical modeling. "
                    "A distributed tiering strategy with horizontal sharding is selected to ensure "
                    "p99 latency compliance within budget boundaries."
                ),
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
                    {"metric": "Daily Volume", "formula": "10000000 * 3 * 500000 / (1024^4)", "result": 13.64, "unit": "TB/day"},
                    {"metric": "Annual Replicated Storage", "formula": "13.64 * 365 * 3", "result": 14935.8, "unit": "TB/year"},
                    {"metric": "Peak Ingress Bandwidth", "formula": "(13.64 * 1024 * 8 / 86400) * 3", "result": 3.88, "unit": "Gbps"},
                ],
                final_answer=(
                    "### Architectural Decision: Tiered Storage & Distributed Ingestion Pipeline\n\n"
                    "1. **Storage Tiering Architecture**:\n"
                    "   - Ingest into hot NVMe/SSD buffer partitioned across distributed brokers.\n"
                    "   - Tier out to cold object storage (S3/GCS Standard) after 7 days, reducing cost by 78%.\n"
                    "   - Provision **15 PB** total raw cloud storage capacity for Year 1.\n\n"
                    "2. **Network & Ingress Bandwidth**:\n"
                    "   - Dual 10 Gbps redundant uplink switches to comfortably handle 3.88 Gbps peak bursts with headroom.\n\n"
                    "3. **Partitioning & Sharding**:\n"
                    "   - Shard by `user_id` hash across 32 logical partitions to distribute write IOPS evenly."
                ),
                trade_offs=[
                    "Triple replication increases storage expenditure by 200% but satisfies 99.999999999% durability SLA.",
                    "Tiering to object storage introduces 100ms retrieval latency for objects older than 7 days.",
                    "Hash sharding complicates global range queries, requiring secondary indexing.",
                ],
                risks=[
                    "Unmonitored viral traffic events exceeding 3x peak multiplier could saturate buffer nodes.",
                    "Cross-region data transfer costs may escalate if replication crosses cloud availability zones.",
                ],
                decision_trace=[
                    {
                        "decision": "Provision 15 PB Annual Object Storage",
                        "constraint": "1-year retention SLA, 3x replication durability",
                        "evidence": "13.64 TB daily ingest * 365 days * 3 replicas = 14,935.8 TB",
                        "calculation": "13.64 * 365 * 3 = 14935.8",
                        "trade_off": "Higher initial cloud cost vs. guaranteed data resilience",
                    },
                    {
                        "decision": "Deploy Dual 10 GbE Ingress Network Interfaces",
                        "constraint": "SLA p99 latency < 200ms during 3x peak bursts",
                        "evidence": "Peak ingress rate measured at 3.88 Gbps",
                        "calculation": "(13.64 * 1024 * 8 / 86400) * 3 = 3.88 Gbps",
                        "trade_off": "Over-provisioned idle bandwidth vs. zero packet drop during traffic spikes",
                    }
                ],
            )

        # Fallback for unexpected schema
        return schema()
