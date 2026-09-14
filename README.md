# EquiSense — AI-Powered Equity Research & Valuation Platform

> An end-to-end platform that automates equity research workflows — from data ingestion to valuation modeling to investment memo generation — using AI/LLM-driven analysis pipelines.

## 📌 Overview

EquiSense combines financial data engineering with large language models to accelerate the equity research process. It ingests company filings, financial statements, and market data, then generates valuation models (DCF, comparable companies, precedent transactions) alongside AI-synthesized research notes — reducing the time analysts spend on repetitive data gathering and enabling faster, more consistent investment decision-making.

Built for analysts, students, and finance professionals who want to combine traditional valuation rigor with modern AI-assisted research.

## ✨ Key Features

- **Automated Data Ingestion** — Pulls financial statements, filings (10-K/10-Q), and market data from public APIs (e.g., SEC EDGAR, Yahoo Finance, Alpha Vantage)
- **AI Research Summarization** — Uses LLMs to summarize earnings calls, MD&A sections, and news sentiment into digestible research notes
- **Valuation Engine**
  - Discounted Cash Flow (DCF) modeling
  - Comparable Company Analysis (Comps)
  - Precedent Transaction Analysis
- **Financial Ratio & Trend Analysis** — Automated computation of liquidity, profitability, leverage, and efficiency ratios
- **Investment Memo Generator** — Auto-drafts research memos combining quantitative outputs with AI-generated qualitative insights
- **Interactive Dashboard** — Visualize valuation sensitivity, peer comparisons, and historical trends
- **Extensible Architecture** — Modular design to plug in new data sources, valuation models, or LLM providers

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│   Data Sources    │ --> │  Ingestion Layer  │ --> │   Data Warehouse    │
│ (SEC, Yahoo, etc) │     │  (ETL Pipelines)  │     │  (Postgres/Parquet) │
└─────────────────┘     └──────────────────┘     └────────────────────┘
                                                            │
                                                            ▼
                                          ┌──────────────────────────────┐
                                          │      Analysis Engine          │
                                          │  - Valuation Models            │
                                          │  - Ratio Calculations          │
                                          │  - LLM Research Agent (RAG)    │
                                          └──────────────────────────────┘
                                                            │
                                                            ▼
                                          ┌──────────────────────────────┐
                                          │     Presentation Layer         │
                                          │  - Dashboard (React/Streamlit) │
                                          │  - Memo Export (PDF/DOCX)      │
                                          │  - REST API                    │
                                          └──────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python (FastAPI) |
| Data Processing | Pandas, NumPy |
| Database | PostgreSQL / SQLite |
| LLM Integration | Anthropic Claude API / OpenAI API |
| Retrieval (RAG) | LangChain / LlamaIndex + Vector DB (Chroma/Pinecone) |
| Frontend | React.js / Streamlit |
| Data Sources | SEC EDGAR API, yFinance, Alpha Vantage |
| Deployment | Docker, GitHub Actions (CI/CD) |

## 📂 Project Structure

```
equisense/
├── data/
│   ├── raw/                  # Raw ingested filings & market data
│   └── processed/            # Cleaned datasets
├── src/
│   ├── ingestion/            # Data connectors (SEC, market APIs)
│   ├── valuation/            # DCF, Comps, Precedent Transaction modules
│   ├── llm_agents/           # AI research & summarization agents
│   ├── ratios/               # Financial ratio calculations
│   ├── memo_generator/       # Investment memo templating & export
│   └── api/                  # FastAPI routes
├── dashboard/                # Frontend app
├── notebooks/                # Exploratory analysis & model prototyping
├── tests/                    # Unit & integration tests
├── configs/                  # Config files (API keys via .env, model settings)
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ (for dashboard)
- API keys: SEC EDGAR (free), Alpha Vantage / Yahoo Finance, Anthropic/OpenAI

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/equisense.git
cd equisense

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your API keys to .env

# Run database migrations
python manage.py migrate

# Start the backend
uvicorn src.api.main:app --reload

# Start the dashboard (separate terminal)
cd dashboard
npm install
npm run dev
```

### Quick Example

```python
from src.valuation.dcf import DCFModel
from src.llm_agents.research_agent import ResearchAgent

# Run a DCF valuation
model = DCFModel(ticker="AAPL", forecast_years=5)
valuation = model.run()
print(f"Estimated Intrinsic Value: ${valuation.per_share_value}")

# Generate an AI research summary
agent = ResearchAgent(ticker="AAPL")
summary = agent.generate_summary()
print(summary)
```

## 📊 Roadmap

- [ ] Add support for international filings (non-US markets)
- [ ] Real-time news sentiment integration
- [ ] Monte Carlo simulation for valuation sensitivity
- [ ] Multi-agent research pipeline (bull case / bear case agents)
- [ ] Portfolio-level analytics
- [ ] Backtesting module for valuation accuracy

## ⚠️ Disclaimer

This tool is intended for educational and research purposes only. It does not constitute financial advice. Valuations generated by this platform rely on assumptions and AI-generated content that may contain errors — always verify with primary sources before making investment decisions.

## 🤝 Contributing

Contributions are welcome! Please open an issue to discuss major changes before submitting a PR.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📬 Contact

Aditya Balaji Makurwar / Ethen
