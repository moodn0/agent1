from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .retrieval import LocalKnowledgeBase, SearchResult

CAPABILITIES = {
    "知识检索与问答": ["知识", "问答", "客服", "文档", "检索", "RAG"],
    "多渠道服务接入": ["微信", "小程序", "网页", "渠道", "工单", "客服"],
    "权限与数据治理": ["权限", "审计", "合规", "隐私", "数据", "脱敏"],
    "运营分析": ["分析", "看板", "报表", "指标", "转化", "运营"],
    "弹性部署与可观测": ["并发", "稳定", "监控", "部署", "SLA", "可用性"],
}


@dataclass
class Requirement:
    category: str
    statement: str
    priority: str


@dataclass
class Proposal:
    requirements: list[Requirement]
    matches: list[tuple[Requirement, str, list[SearchResult]]]
    questions: list[str]
    markdown: str


def _sentences(text: str) -> list[str]:
    return [s.strip(" # -\t") for s in re.split(r"[。！？!？\n]+", text) if len(s.strip(" # -\t")) >= 8]


def analyze_requirements(text: str) -> list[Requirement]:
    found: list[Requirement] = []
    for sentence in _sentences(text):
        hits = [name for name, words in CAPABILITIES.items() if any(word.lower() in sentence.lower() for word in words)]
        priority = "高" if any(word in sentence for word in ("必须", "核心", "关键", "首期", "优先")) else "中"
        for category in hits or ["待进一步确认"]:
            item = Requirement(category, sentence, priority)
            if item not in found:
                found.append(item)
    return found[:10] or [Requirement("待进一步确认", "未能从文档中提取有效需求。", "高")]


def clarification_questions(text: str) -> list[str]:
    questions = []
    checks = [
        ("用户规模", ["用户", "门店", "员工", "坐席"], "首期与峰值并发用户数分别是多少？"),
        ("系统集成", ["系统", "CRM", "ERP", "工单", "接口"], "需要与哪些现有系统集成？是否提供 API 文档和测试环境？"),
        ("数据合规", ["数据", "隐私", "合规", "权限"], "知识库是否包含个人信息或敏感经营数据？数据驻留要求是什么？"),
        ("验收标准", ["效果", "准确", "目标", "指标"], "POC 的业务验收指标、基线和验收负责人分别是谁？"),
    ]
    for _, keywords, question in checks:
        if any(keyword.lower() in text.lower() for keyword in keywords):
            questions.append(question)
    return questions or ["项目的首期范围、预算区间、关键干系人和上线时间表分别是什么？"]


def architecture_mermaid(requirements: list[Requirement]) -> str:
    nodes = ["客户渠道", "应用网关", "AI 编排服务", "企业知识库", "业务系统", "监控审计"]
    return "\n".join([
        "flowchart LR",
        "  A[客户渠道：网页 / 小程序 / 坐席] --> B[应用网关与身份认证]",
        "  B --> C[AI 编排服务]",
        "  C --> D[企业知识库与向量检索]",
        "  C <--> E[CRM / 工单 / 订单系统]",
        "  B --> F[日志、监控与审计]",
        "  C --> F",
    ])


class PresalesWorkflow:
    def __init__(self, knowledge_base_dir: str | Path):
        self.kb = LocalKnowledgeBase(knowledge_base_dir)

    def run(self, rfp_text: str) -> Proposal:
        requirements = analyze_requirements(rfp_text)
        matches = []
        for requirement in requirements:
            evidence = self.kb.search(f"{requirement.category} {requirement.statement}", limit=2)
            solution = self._solution_for(requirement.category)
            matches.append((requirement, solution, evidence))
        proposal = Proposal(requirements, matches, clarification_questions(rfp_text), "")
        proposal.markdown = self._render(proposal)
        return proposal

    @staticmethod
    def _solution_for(category: str) -> str:
        return {
            "知识检索与问答": "部署带引用溯源的企业知识助手，设置知识更新与人工兜底流程。",
            "多渠道服务接入": "通过统一 API 接入客户现有渠道，并将复杂会话转人工或工单。",
            "权限与数据治理": "采用 SSO、角色权限、传输加密与审计日志，并在入库前进行数据分级。",
            "运营分析": "建设会话、命中率、转人工率和业务转化看板，支持按门店/渠道分析。",
            "弹性部署与可观测": "采用容器化部署、限流与全链路监控；按峰值并发完成压测与容量规划。",
        }.get(category, "在澄清范围后进行方案选型与工作量评估。")

    def _render(self, proposal: Proposal) -> str:
        lines = ["# 售前方案初稿", "", "## 1. 需求摘要", ""]
        for item in proposal.requirements:
            lines.append(f"- **[{item.priority}] {item.category}**：{item.statement}")
        lines += ["", "## 2. 需求—方案匹配", "", "| 客户需求 | 建议方案 | 证据来源 |", "|---|---|---|"]
        for req, solution, evidence in proposal.matches:
            citations = "; ".join(f"`{r.source}`" for r in evidence) or "需补充对应产品资料"
            lines.append(f"| {req.category} | {solution} | {citations} |")
        lines += ["", "## 3. 建议 POC", "", "1. **第 1 周：范围与数据准备**——确认 20–50 篇高频知识、访问权限和基线指标。",
                  "2. **第 2 周：原型联调**——完成问答、引用、人工转接与一个业务系统接口。",
                  "3. **第 3 周：试运行与验收**——以正确性、引用覆盖、响应时间和转人工率共同验收。",
                  "", "## 4. 待澄清问题", ""]
        lines.extend(f"- {question}" for question in proposal.questions)
        lines += ["", "## 5. 参考架构", "", "```mermaid", architecture_mermaid(proposal.requirements), "```", "",
                  "## 6. 风险与边界", "", "- 本文为自动生成初稿；产品能力、报价、SLA 与合规承诺须由相关负责人审核。",
                  "- 仅将获得授权且经脱敏的数据用于知识库与测试。"]
        return "\n".join(lines)
