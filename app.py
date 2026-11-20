from pathlib import Path
import tempfile

import streamlit as st

from src.ingestion import read_text
from src.workflow import PresalesWorkflow

ROOT = Path(__file__).parent
st.set_page_config(page_title="PreSales Copilot", page_icon="🧭", layout="wide")
st.title("🧭 PreSales Solution Copilot")
st.caption("上传客户需求，生成带引用的售前方案初稿。请仅使用已获授权、已脱敏的材料。")

sample = (ROOT / "data" / "sample_rfp.md").read_text(encoding="utf-8")
with st.sidebar:
    st.subheader("使用说明")
    st.markdown("1. 粘贴或上传客户需求\n2. 生成可编辑初稿\n3. 核验来源后再对外使用")
    st.divider()
    st.caption("默认知识库为模拟产品资料；不代表真实产品能力、报价或 SLA。")

uploaded = st.file_uploader("上传 RFP（可选）", type=["md", "txt", "docx", "pdf"])
if uploaded:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
        temporary.write(uploaded.getvalue())
        temp_path = Path(temporary.name)
    try:
        text = read_text(temp_path)
        st.success(f"已读取：{uploaded.name}")
    except Exception as error:
        st.error(f"无法读取文件：{error}")
        text = sample
    finally:
        temp_path.unlink(missing_ok=True)
else:
    text = sample

text = st.text_area("客户需求 / RFP", value=text, height=280)
if st.button("生成方案", type="primary"):
    with st.spinner("分析需求、检索知识库并生成方案…"):
        proposal = PresalesWorkflow(ROOT / "data" / "knowledge_base").run(text)
    draft_tab, evidence_tab, checklist_tab = st.tabs(["方案初稿", "引用证据", "售前核验清单"])
    with draft_tab:
        st.markdown(proposal.markdown)
        st.download_button("下载 Markdown 方案", proposal.markdown, "proposal.md", "text/markdown")
    with evidence_tab:
        st.caption("请在提交客户前核对每个引用是否能支撑对应的方案表述。")
        for req, _, results in proposal.matches:
            st.markdown(f"**{req.category}**")
            if not results:
                st.warning("当前知识库没有匹配证据，需要补充产品文档或改为人工确认。")
            for result in results:
                with st.expander(f"{result.source} · 相关度 {result.score}"):
                    st.write(result.excerpt)
    with checklist_tab:
        st.checkbox("已由产品负责人核验产品能力与版本范围")
        st.checkbox("已由商务负责人核验价格、交付范围和 SLA")
        st.checkbox("已确认客户材料经过授权与脱敏")
        st.checkbox("已与客户确认 POC 验收指标和责任人")
