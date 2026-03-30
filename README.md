# 🔬 AI Research Agent

An end-to-end AI agent that automatically searches academic databases, downloads open-access PDFs, summarizes papers using GPT-4, analyzes the literature landscape to identify research gaps, and generates novel management science research ideas.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **Multi-source search** | Semantic Scholar API + arXiv |
| **Automated PDF download** | With retry logic and Unpaywall open-access lookup |
| **PDF text extraction** | PyMuPDF — fast, layout-aware extraction |
| **LLM summarization** | GPT-4 / GPT-4o with structured 6-point summaries |
| **Literature analysis** | Cross-paper synthesis, gap identification, trend detection |
| **Idea generation** | 5 novel, feasible management science research ideas per run |
| **Web UI** | Interactive Streamlit dashboard |
| **CLI** | Full-featured command-line interface |
| **Configurable** | `.env`-based settings for all parameters |
| **Robust** | Comprehensive error handling and logging throughout |

---

## 🏗 Architecture

```
keywords
   │
   ▼
search.py ──────────────────────────────────► paper list
   │ (Semantic Scholar + arXiv)
   ▼
download.py ────────────────────────────────► local PDFs
   │ (requests + retry + Unpaywall fallback)
   ▼
extract.py ─────────────────────────────────► plain text
   │ (PyMuPDF)
   ▼
summarize.py ───────────────────────────────► per-paper summaries
   │ (OpenAI GPT-4)
   ▼
analyze.py ─────────────────────────────────► literature landscape
   │ (OpenAI GPT-4)
   ▼
ideas.py ───────────────────────────────────► novel research ideas
   │ (OpenAI GPT-4, temperature=0.7)
   ▼
agent.py ───────────────────────────────────► JSON report
```

---

## 📁 Project Structure

```
ai-research-agent/
├── agent.py            # Main orchestration pipeline (ResearchAgent class)
├── search.py           # Paper search via Semantic Scholar & arXiv
├── download.py         # PDF downloader with retry logic
├── extract.py          # PDF text extraction (PyMuPDF)
├── summarize.py        # LLM-powered paper summarization
├── analyze.py          # Literature landscape analysis
├── ideas.py            # Novel research idea generation
├── config.py           # Configuration management (.env loader)
├── streamlit_app.py    # Interactive web UI
├── cli.py              # Command-line interface
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # This file
```

---

## 🚀 Quick Start

### 1. Clone and install

```bash
git clone https://github.com/zhanghailun/ai-research-agent.git
cd ai-research-agent
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum
```

### 3. Run the web UI

```bash
streamlit run streamlit_app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Or use the CLI

```bash
# Full pipeline
python cli.py run "supply chain" "sustainability" "circular economy"

# With research context
python cli.py run "digital transformation" "SMEs" \
    --context "Focus on SMEs in developing economies" \
    --max-results 15

# Search only (no LLM)
python cli.py search "operations management" --limit 10

# Summarize a single PDF
python cli.py summarize path/to/paper.pdf --title "My Paper"

# View a saved report
python cli.py report output/report_supply-chain_20240101_120000.json
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and edit:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Model name |
| `SEMANTIC_SCHOLAR_API_KEY` | *(optional)* | Higher rate limits |
| `UNPAYWALL_EMAIL` | `research@example.com` | Required for Unpaywall lookups |
| `PAPERS_DIR` | `papers` | Where PDFs are saved |
| `OUTPUT_DIR` | `output` | Where JSON reports are saved |
| `DEFAULT_MAX_RESULTS` | `20` | Papers per source |
| `DOWNLOAD_TIMEOUT` | `30` | Seconds per HTTP request |
| `DOWNLOAD_RETRIES` | `3` | Download retry attempts |
| `DOWNLOAD_BACKOFF` | `2.0` | Exponential backoff base |
| `SUMMARIZE_MAX_TOKENS` | `1500` | LLM tokens for summaries |
| `ANALYSIS_MAX_TOKENS` | `2000` | LLM tokens for analysis |
| `IDEAS_MAX_TOKENS` | `2500` | LLM tokens for ideas |
| `PDF_TEXT_LIMIT` | `12000` | Characters sent to LLM per paper |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LOG_FILE` | *(none)* | Optional log file path |

---

## 🐍 Python API

```python
from agent import ResearchAgent

agent = ResearchAgent()
report = agent.run(
    keywords=["supply chain", "sustainability", "circular economy"],
    research_context="Focus on circular economy practices in manufacturing",
    max_results=15,
    skip_download=False,   # Set True to summarize from abstracts only
)

print(report["literature_analysis"])
print(report["novel_ideas"])

# Access individual paper summaries
for paper in report["papers"]:
    print(paper["title"], "—", paper["summary"][:200])
```

### Individual modules

```python
# Search only
from search import search_all
papers = search_all(["digital platforms", "SMEs"], limit=10)

# Download PDFs
from download import download_papers
papers = download_papers(papers)

# Extract text
from extract import extract_text
text, metadata = extract_text("papers/001_my_paper.pdf")

# Summarize a single paper
from summarize import summarize_paper
summary = summarize_paper(text=text, title="My Paper", abstract="...")

# Analyze literature
from analyze import analyze_literature
analysis = analyze_literature(papers, keywords=["digital platforms"])

# Generate ideas
from ideas import generate_ideas
ideas = generate_ideas(analysis, keywords=["digital platforms"], research_context="B2B focus")
```

---

## 📊 Example Output

### Literature Analysis (excerpt)

```
1. **Common Themes**: Sustainable supply chain management (SSCM) consistently emerges
   as a dominant theme, with particular focus on carbon footprint reduction and ...

2. **Dominant Methodologies**: Quantitative empirical methods (regression, SEM) account
   for ~65% of studies. Simulation and mathematical modelling represent 20%...

5. **Research Gaps**: (1) Limited studies in SME contexts; (2) Long-term longitudinal
   evidence is scarce; (3) Institutional factors in emerging markets under-explored...
```

### Novel Research Ideas (excerpt)

```
**Idea 1: Circular Economy Adoption in B2B Supply Chains: An Institutional Theory Perspective**

- **Research Question**: How do coercive, mimetic, and normative institutional pressures
  drive CE adoption heterogeneity across B2B supply chain tiers?
- **Novelty & Gap**: While prior work examines CE adoption at firm level, cross-tier
  institutional dynamics remain unexplored...
- **Proposed Methodology**: Multi-wave longitudinal survey (N≈500 firms), SEM + HLM...
- **Potential Journals**: Management Science, Journal of Operations Management, MSOM
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|---------|
| `OPENAI_API_KEY not set` | Add key to `.env` or pass in Streamlit sidebar |
| No PDFs downloaded | Papers may not be open-access; use `--skip-download` |
| Rate limit errors | Reduce `DEFAULT_MAX_RESULTS` or add `SEMANTIC_SCHOLAR_API_KEY` |
| PyMuPDF install fails | Ensure your platform is supported: `pip install PyMuPDF` |
| Empty summaries | Increase `PDF_TEXT_LIMIT` or check paper text quality |

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Semantic Scholar API](https://api.semanticscholar.org/)
- [arXiv API](https://arxiv.org/help/api/)
- [Unpaywall](https://unpaywall.org/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [OpenAI](https://platform.openai.com/)
- [Streamlit](https://streamlit.io/)
