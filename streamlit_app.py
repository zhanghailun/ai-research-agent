"""
streamlit_app.py — Interactive web UI for the AI Research Agent.

Run with:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st

import config

config.setup_logging()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

st.sidebar.title("⚙️ Configuration")

poe_key = st.sidebar.text_input(
    "POE API Key",
    value=config.POE_API_KEY or "",
    type="password",
    help="Required for summarization and idea generation. Get your key at https://poe.com/api_key.",
)
if poe_key:
    config.POE_API_KEY = poe_key

poe_bot = st.sidebar.selectbox(
    "POE Bot / Model",
    options=[
        "Claude-3.5-Sonnet",
        "Claude-3-Opus",
        "Claude-3-Haiku",
        "GPT-4o",
        "GPT-4",
        "GPT-3.5-Turbo",
    ],
    index=0,
    help="The POE bot to use for summarization and analysis.",
)
config.POE_BOT_NAME = poe_bot

st.sidebar.markdown("---")

max_results = st.sidebar.slider(
    "Max papers per source",
    min_value=5,
    max_value=50,
    value=config.DEFAULT_MAX_RESULTS,
    step=5,
)

sources_selected = st.sidebar.multiselect(
    "Search Sources",
    options=["semantic_scholar", "arxiv", "ssrn"],
    default=["semantic_scholar", "arxiv", "ssrn"],
)

skip_download = st.sidebar.checkbox(
    "Skip PDF download (use abstracts only)",
    value=False,
    help="Faster but less detailed — summarizes from abstract only.",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**AI Research Agent** v1.0  \n"
    "[GitHub](https://github.com/zhanghailun/ai-research-agent)"
)

# ---------------------------------------------------------------------------
# Main — title & intro
# ---------------------------------------------------------------------------

st.title("🔬 AI Research Agent")
st.markdown(
    "Automatically search academic databases, summarize papers, analyse the literature "
    "landscape, and generate novel management science research ideas."
)

# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------

col1, col2 = st.columns([2, 1])

with col1:
    keywords_input = st.text_input(
        "Research Keywords",
        placeholder="e.g. supply chain sustainability circular economy",
        help="Enter keywords separated by spaces. The agent will search for papers matching all keywords.",
    )

with col2:
    research_context = st.text_area(
        "Research Context (optional)",
        placeholder="e.g. Focus on SMEs in developing countries",
        height=100,
    )

run_button = st.button("🚀 Run Research Pipeline", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

if run_button:
    if not keywords_input.strip():
        st.error("Please enter at least one keyword.")
        st.stop()

    if not config.POE_API_KEY:
        st.warning(
            "No POE API key provided. Summarization and idea generation will fail. "
            "Enter your key in the sidebar (get it at poe.com/api_key)."
        )

    keywords = [kw.strip() for kw in keywords_input.split() if kw.strip()]
    st.info(f"🔍 Running research for keywords: **{', '.join(keywords)}**")

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Step-by-step pipeline with visual feedback
    try:
        from search import search_all

        status_text.text("Step 1/6 — Searching for papers…")
        progress_bar.progress(5)
        papers = search_all(keywords, limit=max_results, sources=sources_selected or None)
        progress_bar.progress(20)
        st.success(f"✅ Found **{len(papers)}** papers")

        if not skip_download:
            from download import download_papers

            status_text.text("Step 2/6 — Downloading PDFs…")
            papers = download_papers(papers)
            progress_bar.progress(40)
            pdfs = sum(1 for p in papers if p.get("local_pdf"))
            st.success(f"✅ Downloaded **{pdfs}** PDFs")
        else:
            for p in papers:
                p.setdefault("local_pdf", "")
            progress_bar.progress(40)

        from extract import extract_papers

        status_text.text("Step 3/6 — Extracting text…")
        papers = extract_papers(papers)
        progress_bar.progress(55)

        from summarize import summarize_papers

        status_text.text("Step 4/6 — Summarizing papers (this may take a few minutes)…")
        papers = summarize_papers(papers)
        progress_bar.progress(70)
        summarized = sum(1 for p in papers if p.get("summary") and not p["summary"].startswith("["))
        st.success(f"✅ Summarized **{summarized}** papers")

        from analyze import analyze_literature

        status_text.text("Step 5/6 — Analyzing literature landscape…")
        literature_analysis = analyze_literature(papers, keywords=keywords)
        progress_bar.progress(85)

        from ideas import generate_ideas

        status_text.text("Step 6/6 — Generating novel research ideas…")
        novel_ideas = generate_ideas(
            literature_analysis,
            keywords=keywords,
            research_context=research_context,
        )
        progress_bar.progress(100)
        status_text.text("✅ Pipeline complete!")

        # ── Store results in session state ──────────────────────────────
        st.session_state["papers"] = papers
        st.session_state["literature_analysis"] = literature_analysis
        st.session_state["novel_ideas"] = novel_ideas
        st.session_state["keywords"] = keywords

    except Exception as exc:
        st.error(f"Pipeline error: {exc}")
        import traceback
        st.exception(exc)

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

if "papers" in st.session_state:
    papers = st.session_state["papers"]
    literature_analysis = st.session_state.get("literature_analysis", "")
    novel_ideas = st.session_state.get("novel_ideas", "")
    keywords = st.session_state.get("keywords", [])

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📚 Papers", "🔍 Literature Analysis", "💡 Novel Ideas", "📥 Export"]
    )

    # ── Tab 1: Papers ─────────────────────────────────────────────────
    with tab1:
        st.subheader(f"Papers Found ({len(papers)})")
        for i, p in enumerate(papers, start=1):
            with st.expander(
                f"{i}. [{p.get('year', '?')}] {p.get('title', 'Untitled')} — {p.get('source', '')}"
            ):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    authors = ", ".join(p.get("authors", [])[:5])
                    if len(p.get("authors", [])) > 5:
                        authors += " et al."
                    st.markdown(f"**Authors:** {authors}")
                    if p.get("abstract"):
                        st.markdown(f"**Abstract:** {p['abstract'][:400]}…")
                with col_b:
                    if p.get("url"):
                        st.markdown(f"[🔗 Paper page]({p['url']})")
                    if p.get("open_access_pdf"):
                        st.markdown(f"[📄 PDF]({p['open_access_pdf']})")
                    pdf_icon = "✅" if p.get("local_pdf") else "❌"
                    st.markdown(f"PDF downloaded: {pdf_icon}")

                if p.get("summary"):
                    st.markdown("---")
                    st.markdown("**Summary:**")
                    st.markdown(p["summary"])

    # ── Tab 2: Literature Analysis ────────────────────────────────────
    with tab2:
        st.subheader("Literature Landscape Analysis")
        if literature_analysis:
            st.markdown(literature_analysis)
        else:
            st.info("Run the pipeline to see the analysis.")

    # ── Tab 3: Novel Ideas ────────────────────────────────────────────
    with tab3:
        st.subheader("Novel Management Science Research Ideas")
        if novel_ideas:
            st.markdown(novel_ideas)
        else:
            st.info("Run the pipeline to see generated ideas.")

    # ── Tab 4: Export ─────────────────────────────────────────────────
    with tab4:
        st.subheader("Export Results")
        report = {
            "keywords": keywords,
            "papers_found": len(papers),
            "literature_analysis": literature_analysis,
            "novel_ideas": novel_ideas,
            "papers": [
                {k: v for k, v in p.items() if k != "extracted_text"}
                for p in papers
            ],
        }
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        st.download_button(
            label="⬇️ Download JSON Report",
            data=report_json,
            file_name=f"research_report_{'_'.join(keywords[:3])}.json",
            mime="application/json",
        )

        st.markdown("**Markdown report:**")
        md_lines = [
            f"# Research Report: {', '.join(keywords)}\n",
            "## Literature Analysis\n",
            literature_analysis or "N/A",
            "\n## Novel Research Ideas\n",
            novel_ideas or "N/A",
            "\n## Papers\n",
        ]
        for i, p in enumerate(papers, start=1):
            md_lines.append(f"### {i}. {p.get('title', 'Untitled')}")
            md_lines.append(
                f"- **Year**: {p.get('year', 'N/A')}  \n"
                f"- **Authors**: {', '.join(p.get('authors', [])[:5])}  \n"
                f"- **Source**: {p.get('source', 'N/A')}  \n"
            )
            if p.get("summary"):
                md_lines.append(f"**Summary:**\n{p['summary']}\n")

        md_report = "\n".join(md_lines)
        st.download_button(
            label="⬇️ Download Markdown Report",
            data=md_report,
            file_name=f"research_report_{'_'.join(keywords[:3])}.md",
            mime="text/markdown",
        )
