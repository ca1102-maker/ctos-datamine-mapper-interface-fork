# Frederick Platform

Medical terminology mapping platform built on Neo4j, Streamlit, and LangChain.
Maps raw clinical data terms to standardized NCIT/caDSR terminology via exact,
fuzzy, and semantic search.

## Project structure

```
frederick/
├── app/
│   ├── main.py                  # Streamlit entrypoint + router + sidebar
│   ├── styles.py                # All shared CSS
│   ├── pages/                   # One file per page
│   │   ├── home.py              # Chat + quick nav
│   │   ├── map_and_grade.py     # Batch mapping + inline SME grading (Sprint 12)
│   │   ├── graph_explore.py     # Graph Query + Visualization (merged)
│   │   ├── ingest.py            # EVS file upload → Neo4j ingestion
│   │   ├── dashboard.py         # KPI overview
│   │   └── settings.py          # Connection info, system prompt, preferences
│   ├── components/
│   │   └── sidebar.py           # Sidebar: status, model config, nav
│   └── services/
│       ├── neo4j_client.py      # BackendClient (Neo4j + kg_toolkit)
│       └── models.py            # MatchResult, GraphPayload dataclasses
├── assets/
│   ├── icon.png
│   └── logo.png
├── config/
│   └── eg.env                   # Example .env
├── ncit-semantic-mapper/        # kg_toolkit library (git submodule)
├── si-tamer/                    # si_tamer library (git submodule)
├── requirements.txt             # Python deps for the Streamlit app
└── README.md
```

## Quickstart (Anvil)

```bash
# 1. Clone & enter
cd /path/to/frederick

# 2. Copy env and fill in credentials
cp config/eg.env .env

# 3. Install deps
pip install -r requirements.txt

# 4. Ensure ncit-semantic-mapper is on PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/ncit-semantic-mapper/src

# 5. Run
streamlit run app/main.py
```

## Key changes from Sprint 11 → Sprint 12

- **Merged Semantic Mapping + SME Workbench** into a single "Map & Grade" page
  with batch CSV upload, table-view results, and inline grading.
- **Merged Graph Query + Graph Visualization** into a single "Explore Graph" page.
- **Restructured** the monolithic `app_wired.py` (1350 lines) into focused modules.
- **Removed** dead code: `frontend/` (old React mock), `backend/` (unused FastAPI
  scaffold), duplicate Streamlit files (`streamlit_old.py`, `streamlitlog.py`, etc.).
