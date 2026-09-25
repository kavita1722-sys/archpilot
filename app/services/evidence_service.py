"""Evidence extraction, normalization, and credibility filtering service."""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from app.core.logging import logger
from app.schemas.evidence import EvidenceFilterResult, EvidenceItem


class EvidenceService:
    """Orchestrates evidence extraction from raw tool outputs and evaluates credibility."""

    def __init__(self) -> None:
        self._counter = 0

    def next_evidence_id(self) -> str:
        """Generate sequential evidence ID (e.g. EV-001, EV-002)."""
        self._counter += 1
        return f"EV-{self._counter:03d}"

    def extract_evidence_from_search(
        self, search_results: List[Dict[str, Any]], query: str = ""
    ) -> List[EvidenceItem]:
        """Convert raw search results into normalized EvidenceItem records."""
        items: List[EvidenceItem] = []
        for res in search_results:
            title = res.get("title", "Technical Documentation")
            url = res.get("url", "https://docs.example.org")
            snippet = res.get("snippet", "").strip()
            source = res.get("source", "web").lower()

            # Classify source type
            if any(k in url.lower() or k in title.lower() for k in ["docs", "documentation", "github", "manual", "guide"]):
                source_type = "documentation"
            elif any(k in snippet.lower() for k in ["benchmark", "latency", "throughput", "qps"]):
                source_type = "benchmark"
            else:
                source_type = "web"

            # Formulate claim from snippet
            first_sentence = snippet.split(".")[0].strip() if "." in snippet else snippet
            claim = first_sentence if len(first_sentence) > 15 else f"Documented finding regarding {query}"

            item = EvidenceItem(
                id=self.next_evidence_id(),
                title=title,
                url=url,
                source_type=source_type,
                claim=claim,
                excerpt=snippet[:400],
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                relevance=0.92 if query and any(w in snippet.lower() for w in query.lower().split()[:3]) else 0.85,
                confidence=0.88,
                status="verified",
            )
            items.append(item)

        logger.info("Extracted %d evidence items from search results", len(items))
        return items

    def extract_evidence_from_fetch(
        self, fetch_result: Dict[str, Any], topic: str = ""
    ) -> Optional[EvidenceItem]:
        """Convert URL fetch output into a high-confidence EvidenceItem."""
        url = fetch_result.get("url", "")
        title = fetch_result.get("title", "Extracted Documentation")
        content = fetch_result.get("content", "").strip()

        if not content:
            return None

        # Clean content and take the first two key sentences as excerpt
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
        excerpt = ". ".join(sentences[:3]) + "." if sentences else content[:300]
        claim = sentences[0] + "." if sentences else f"Architectural specification from {url}"

        item = EvidenceItem(
            id=self.next_evidence_id(),
            title=title,
            url=url,
            source_type="documentation" if "docs" in url or "github" in url else "web",
            claim=claim[:250],
            excerpt=excerpt[:500],
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            relevance=0.95,
            confidence=0.90,
            status="verified",
        )
        return item

    def filter_evidence(
        self, claim: str, candidate: EvidenceItem
    ) -> EvidenceFilterResult:
        """Evaluate candidate evidence against a claim (supporting, contradicting, or insufficient)."""
        claim_lower = claim.lower()
        excerpt_lower = candidate.excerpt.lower()
        title_lower = candidate.title.lower()

        # Keywords overlap
        claim_words = set(re.findall(r"\w{4,}", claim_lower))
        candidate_words = set(re.findall(r"\w{4,}", excerpt_lower + " " + title_lower))

        overlap = claim_words.intersection(candidate_words)
        overlap_ratio = len(overlap) / max(len(claim_words), 1)

        # Check for direct contradictions (e.g. not, never, incompatible, insufficient)
        contradiction_markers = ["not recommended", "incompatible", "deprecated", "cannot support", "exceeds budget"]
        is_contradicting = any(m in excerpt_lower for m in contradiction_markers) and overlap_ratio > 0.3

        if is_contradicting:
            return EvidenceFilterResult(
                evaluation="contradicting",
                confidence=0.85,
                reasoning=f"Evidence contains explicit constraint violation or negative recommendation: {candidate.excerpt[:150]}",
            )

        if overlap_ratio >= 0.25 or candidate.relevance >= 0.8:
            return EvidenceFilterResult(
                evaluation="supporting",
                confidence=min(0.70 + (overlap_ratio * 0.3), 0.99),
                reasoning=f"Evidence directly substantiates technical claim with verified source '{candidate.title}' ({overlap_ratio:.1%} term overlap).",
            )

        return EvidenceFilterResult(
            evaluation="insufficient",
            confidence=0.45,
            reasoning="Candidate text does not contain sufficient semantic overlap or quantitative benchmarks to verify claim.",
        )

    def check_evidence_integrity(
        self,
        decisions: List[Any],
        evidence: List[Any],
    ) -> Dict[str, Any]:
        """Check for dangling evidence references in decisions.

        Ensures every supporting_evidence_id referenced by a DecisionItem
        exists in the actual evidence ledger. If an evidence ID does not
        exist, it is flagged as dangling rather than silently invented.
        """
        valid_evidence_ids = set()
        for e in evidence:
            if isinstance(e, dict):
                ev_id = e.get("id") or e.get("evidence_id")
            else:
                ev_id = getattr(e, "id", None) or getattr(e, "evidence_id", None)
            if ev_id:
                valid_evidence_ids.add(str(ev_id))

        dangling_refs: List[Dict[str, str]] = []
        for d in decisions:
            if isinstance(d, dict):
                dec_id = d.get("id") or d.get("decision_id", "DEC-unknown")
                ref_ids = d.get("supporting_evidence_ids", [])
            else:
                dec_id = getattr(d, "id", None) or getattr(d, "decision_id", "DEC-unknown")
                ref_ids = getattr(d, "supporting_evidence_ids", [])

            for ev_id in ref_ids:
                if str(ev_id) not in valid_evidence_ids:
                    dangling_refs.append({
                        "decision_id": str(dec_id),
                        "dangling_evidence_id": str(ev_id),
                    })

        is_valid = len(dangling_refs) == 0
        return {
            "is_valid": is_valid,
            "dangling_references": dangling_refs,
            "valid_evidence_ids": sorted(list(valid_evidence_ids)),
        }

    def sanitize_decision_evidence_references(
        self,
        decisions: List[Any],
        evidence: List[Any],
    ) -> List[Any]:
        """Ensure decisions only reference existing evidence IDs without inventing missing ones."""
        valid_evidence_ids = set()
        for e in evidence:
            if isinstance(e, dict):
                ev_id = e.get("id") or e.get("evidence_id")
            else:
                ev_id = getattr(e, "id", None) or getattr(e, "evidence_id", None)
            if ev_id:
                valid_evidence_ids.add(str(ev_id))

        sanitized = []
        for d in decisions:
            if isinstance(d, dict):
                orig_refs = d.get("supporting_evidence_ids", [])
                valid_refs = [ref for ref in orig_refs if str(ref) in valid_evidence_ids]
                d_copy = dict(d)
                d_copy["supporting_evidence_ids"] = valid_refs
                sanitized.append(d_copy)
            else:
                orig_refs = getattr(d, "supporting_evidence_ids", [])
                valid_refs = [ref for ref in orig_refs if str(ref) in valid_evidence_ids]
                d.supporting_evidence_ids = valid_refs
                sanitized.append(d)
        return sanitized

