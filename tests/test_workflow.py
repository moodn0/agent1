import unittest
from pathlib import Path

from src.workflow import PresalesWorkflow, analyze_requirements
from src.evaluate import evaluate


ROOT = Path(__file__).parents[1]


class WorkflowTests(unittest.TestCase):
    def test_requirement_extraction(self):
        requirements = analyze_requirements("首期必须支持知识问答，并按角色设置权限和审计日志。")
        categories = {item.category for item in requirements}
        self.assertIn("知识检索与问答", categories)
        self.assertIn("权限与数据治理", categories)

    def test_proposal_has_evidence_and_architecture(self):
        workflow = PresalesWorkflow(ROOT / "data" / "knowledge_base")
        proposal = workflow.run("客户必须上线知识问答客服，并要求权限、审计和高峰期监控。")
        self.assertIn("需求—方案匹配", proposal.markdown)
        self.assertIn("```mermaid", proposal.markdown)
        self.assertTrue(any(results for _, _, results in proposal.matches))

    def test_evaluation_reports_grounding_metrics(self):
        metrics = evaluate(ROOT / "data" / "knowledge_base", ROOT / "data" / "sample_rfp.md")
        self.assertGreater(metrics["requirements_extracted"], 0)
        self.assertGreater(metrics["citation_coverage"], 0)


if __name__ == "__main__":
    unittest.main()
