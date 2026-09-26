# ArchPilot Contest Demonstration — Sample Input

This document provides the canonical contest demonstration input for **ArchPilot**, an evidence-driven AI agent for systems engineering decisions.

---

## 1. Problem Statement

> **Engineering Challenge**:  
> "Design an architecture for a private RAG platform that must ingest 100,000 PDF documents, support 20 concurrent users, maintain strict data privacy, and stay within a constrained infrastructure budget. Compare architecture alternatives, calculate capacity requirements, identify risks, and provide an implementation roadmap."

---

## 2. API Request Payload

Submit this payload via `POST /api/v1/runs`:

```json
{
  "task": "Design an architecture for a private RAG platform that must ingest 100,000 PDF documents, support 20 concurrent users, maintain strict data privacy, and stay within a constrained infrastructure budget. Compare architecture alternatives, calculate capacity requirements, identify risks, and provide an implementation roadmap.",
  "constraints": {
    "document_count": 100000,
    "concurrency_target": 20,
    "privacy_level": "strict_private_vpc",
    "monthly_budget_usd": 600,
    "target_p95_latency_ms": 1500,
    "data_egress": "zero_third_party_egress"
  }
}
```

---

## 3. Terminal / cURL Command

```bash
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design an architecture for a private RAG platform that must ingest 100,000 PDF documents, support 20 concurrent users, maintain strict data privacy, and stay within a constrained infrastructure budget. Compare architecture alternatives, calculate capacity requirements, identify risks, and provide an implementation roadmap.",
    "constraints": {
      "document_count": 100000,
      "concurrency_target": 20,
      "privacy_level": "strict_private_vpc",
      "monthly_budget_usd": 600
    }
  }'
```

---

## 4. Execution Command in UI

1. Open the ArchPilot UI at `http://localhost:8501`.
2. In the **Create Run** view, paste the task prompt above.
3. Add constraints for document count (`100000`), concurrency (`20`), privacy (`strict`), and budget (`600`).
4. Click **Start Engineering Run**.
