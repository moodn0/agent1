"""Small reproducible evaluation for the portfolio demo's grounding behavior."""
from __future__ import annotations

import json
from pathlib import Path

from .ingestion import read_text
from .workflow import PresalesWorkflow


def evaluate(knowledge_base: str | Path, rfp: str | Path) -> dict[str, object]:
    proposal = PresalesWorkflow(knowledge_base).run(read_text(rfp))
    matched = sum(bool(evidence) for _, _, evidence in proposal.matches)
    total = len(proposal.matches)
    return {
        "requirements_extracted": len(proposal.requirements),
        "recommendations_generated": total,
        "recommendations_with_evidence": matched,
        "citation_coverage": round(matched / total, 3) if total else 0.0,
        "clarification_questions": len(proposal.questions),
    }


def main() -> None:
    root = Path(__file__).parents[1]
    metrics = evaluate(root / "data" / "knowledge_base", root / "data" / "sample_rfp.md")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
