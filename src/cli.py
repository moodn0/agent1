from __future__ import annotations

import argparse
from pathlib import Path

from .ingestion import read_text
from .llm import OpenAICompatibleRefiner
from .workflow import PresalesWorkflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a traceable presales proposal draft.")
    parser.add_argument("--input", required=True, help="Customer RFP: md/txt/docx/pdf")
    parser.add_argument("--output", default="artifacts/proposal.md")
    parser.add_argument("--knowledge-base", default="data/knowledge_base")
    parser.add_argument("--refine-summary", action="store_true", help="Use an optional OpenAI-compatible endpoint for a summary.")
    args = parser.parse_args()
    proposal = PresalesWorkflow(args.knowledge_base).run(read_text(args.input))
    if args.refine_summary:
        facts = "\n".join(f"- {item.category}: {item.statement}" for item in proposal.requirements)
        summary = OpenAICompatibleRefiner().executive_summary(facts)
        proposal.markdown = proposal.markdown.replace("## 1. 需求摘要", f"## 0. 管理层摘要\n\n{summary}\n\n## 1. 需求摘要")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(proposal.markdown, encoding="utf-8")
    print(f"Proposal created: {output}")


if __name__ == "__main__":
    main()
