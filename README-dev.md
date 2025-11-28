# **Chile Data Visual Explorer**

**One-line**: Interactive data-visualization explorer combining public financial, macroeconomic, commodity, ESG and regional datasets focused on companies and markets connected to Chile.

## **Goals**

- Demonstrate end-to-end data engineering & visualization using public data sources.

- Provide reusable modules: data fetchers, ETL, plotting utilities, and an interactive Streamlit dashboard.

- Showcase analyses relevant to Chile: exchange rate, copper & lithium linkages, and corporate ESG trends.

Example data sources

- Stock prices: yfinance (Yahoo Finance) — free historical quotes for Chilean-listed tickers and ADRs.

- Central Bank of Chile (BCCh): official macro series (USDCLP, IPC, IMACEC, interest rates).

- TradingEconomics / public CSVs: commodity prices (copper, lithium).

- INE Chile / data.gob.cl: labor, demographic, regional statistics.

- Company reports: PDF-based ESG & sustainability reports (extracted with tabula-py / pdfminer.six).

Suggested companies (can be edited)
    
    Falabella (FALABELLA.SN)
    Cencosud (CENCOSUD.SN)
    SQM (SQM-A / SQM-B)
    LATAM Airlines (LTM.SN)
    Banco de Chile (CHILE.SN)
    Enel Américas (ENELAM.SN)
    CMPC (CMPC.SN)
    CAP (CAP.SN)

Repo structure
```
chile-data-visual-explorer/
├── data/                   # raw & processed datasets (gitignored raw)
│   ├── raw/
│   └── processed/
├── notebooks/              # Jupyter notebooks for exploration
├── src/
│   ├── data_fetch/         # API wrappers and fetch scripts
│   ├── etl/                # cleaning & processing pipelines
│   ├── viz/                # plotting helper functions
│   └── dashboard/          # Streamlit app
├── dashboards/             # exported dashboard pages/screenshots
├── requirements.txt
├── README.md
└── LICENSE
```

### **Getting started (developer)**

Create a virtual environment and install dependencies:

`python -m venv .venv`

`source .venv/bin/activate` or `.venv\Scripts\activate` on Windows

`pip install -r requirements.txt`