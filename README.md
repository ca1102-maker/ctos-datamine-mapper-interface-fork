# 🧬 Frederick Platform

Medical terminology mapping platform built on **Neo4j**, **Streamlit**, and **LangChain**.
Maps raw clinical data terms to standardized NCIT/caDSR terminology via exact, fuzzy, synonym, and semantic search — with a built-in LLM agent for conversational querying.

---

## Features

- **User Authentication** — Per-user accounts stored as `PlatformUser` nodes in Neo4j. Login/signup on startup; chat histories are scoped to each user via `(PlatformUser)-[:OWNS]->(ChatSession)`.
- **AI Chat (Home)** — Conversational interface with smart routing: Ollama agent → Claude API → mock fallback. Chat sessions persist in Neo4j with full message history. Supports creating, loading, and deleting chats.
- **Map & Grade** — Batch CSV upload for mapping raw terms to NCIT/caDSR. Table-view results with inline SME grading.
- **Explore Graph** — Natural language → Cypher query generation. Interactive knowledge graph visualization.
- **Benchmark** — Upload EVS ground-truth files and compare Frederick's search cascade accuracy (exact → fuzzy → synonym → semantic) against EVS baseline. Exportable results with filtering.
- **Dashboard** — KPI overview and system metrics.
- **Ingest Data** — Upload EVS result files (.tsv) directly into Neo4j.
- **Settings** — Connection info, system prompt editor, preferences.
- **Ollama Model Discovery** — Sidebar auto-detects locally installed Ollama models via API. Dropdown selection for both the reasoning agent and Cypher generation model.

---

## Project Structure

```
frederick/
├── app/
│   ├── main.py                  # Streamlit entrypoint, auth gate, router
│   ├── styles.py                # Shared CSS
│   ├── components/
│   │   └── sidebar.py           # Status, Ollama model picker, nav, logout
│   ├── views/
│   │   ├── login.py             # Login / create account page
│   │   ├── home.py              # AI chat + chat history (user-scoped)
│   │   ├── map_and_grade.py     # Batch mapping + inline SME grading
│   │   ├── graph_explore.py     # NL-to-Cypher + graph visualization
│   │   ├── benchmark.py         # Frederick vs EVS accuracy benchmark
│   │   ├── dashboard.py         # KPI overview
│   │   ├── ingest.py            # EVS file upload → Neo4j
│   │   └── settings.py          # Connection info, preferences
│   └── services/
│       ├── neo4j_client.py      # BackendClient (Neo4j, kg_toolkit, auth, chat)
│       └── models.py            # MatchResult, GraphPayload dataclasses
├── assets/
│   ├── icon.png
│   └── logo.png
├── config/
│   └── eg.env                   # Example environment variables
├── ncit-semantic-mapper/        # kg_toolkit library (submodule)
├── si-tamer/                    # si_tamer library (submodule)
├── ollama_setup.sh              # One-time Ollama setup script for Anvil
├── requirements.txt
└── README.md
```

---

## Neo4j Schema

### Application Nodes

| Label | Properties | Purpose |
|-------|-----------|---------|
| `PlatformUser` | `user_id`, `username`, `display_name`, `pw_hash`, `pw_salt`, `created_at` | User accounts |
| `ChatSession` | `chat_id`, `title`, `created_at`, `updated_at` | Conversation sessions |
| `ChatMessage` | `message_id`, `chat_id`, `role`, `content`, `position`, `created_at` | Individual messages |
| `UploadFile` | `file_id`, `filename`, `source`, `uploaded_at`, `row_count` | Ingested EVS files |
| `UploadRow` | `row_id`, `file_id`, `row_index`, `raw_line`, ... | Parsed rows from uploads |

### Application Relationships

| Relationship | Pattern |
|-------------|---------|
| `OWNS` | `(PlatformUser)-[:OWNS]->(ChatSession)` |
| `HAS_MESSAGE` | `(ChatSession)-[:HAS_MESSAGE]->(ChatMessage)` |
| `HAS_ROW` | `(UploadFile)-[:HAS_ROW]->(UploadRow)` |

### Knowledge Graph Nodes

| Label | Description |
|-------|------------|
| `CDE` | Common Data Element (code, term, definition) |
| `DEC` | Data Element Concept |
| `NCIT` | NCI Thesaurus Concept |
| `OC` | Object Class |
| `PR` | Property / Attribute |
| `PV` | Permissible Value |
| `VDM` | Value Domain |
| `SYN` | Synonym |

### Knowledge Graph Relationships

```
(CDE)-[:HAS_VDM]->(VDM)-[:HAS_PV]->(PV)-[:HAS_CONCEPT]->(NCIT)-[:HAS_SYNONYM]->(SYN)
(CDE)-[:HAS_DEC]->(DEC)-[:HAS_OC]->(OC)
                       -[:HAS_PR]->(PR)
```

---

## Quickstart (Anvil / Purdue HPC)

### Prerequisites

- Python 3.10+
- Access to the Neo4j instance at `fnl-llm-neo4j.tdm.gedges.rcac.purdue.edu`
- (Optional) Ollama installed for local LLM inference
- (Optional) Anthropic API key for Claude fallback

### 1. Clone & enter

```bash
git clone <repo-url>
cd frederick
```

### 2. Set up environment variables

```bash
cp config/eg.env .env
# Edit .env with your credentials:
#   NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
#   ANTHROPIC_API_KEY (optional, for Claude fallback)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Ollama (one-time, optional)

Request a high computer server (e.g. DatamineMAX VSCode 128 cores), could potentially run on smaller datamine 16 node session, but VERY slowly

```bash
chmod +x ollama_setup.sh
./ollama_setup.sh
```

This symlinks model storage to `$SCRATCH`, pulls models (`qwen3`, `nomic-embed-text`), and creates thread-limited variants. Models persist across sessions — you only need to run `ollama serve &` on future logins.

### 5. Run the app

```bash
./run.sh
```

The app opens with a login page. Create an account to get started — your chat history will be saved to your account in Neo4j.

---

## LLM Routing

The platform uses a three-tier fallback for chat responses:

1. **Ollama agent** (local) — Uses the model selected in the sidebar. Full tool-calling agent with access to exact match, synonym, fuzzy, and semantic search tools.
2. **Claude API** (remote) — Falls back here if Ollama is unavailable. Requires `ANTHROPIC_API_KEY` in `.env`.
3. **Mock response** — Placeholder when both are down.

The sidebar auto-detects installed Ollama models and lets you swap between them without restarting.

---

## Benchmark

The Benchmark page (`🏆 Benchmark` in sidebar) compares Frederick's mapping accuracy against EVS ground truth:

1. Upload a CDA/EVS summary TSV file
2. Frederick runs its search cascade (exact → fuzzy → synonym → semantic) on each term
3. Results show #1 hit rate, top-K hit rate, and head-to-head comparison vs EVS
4. Filter by "Frederick wins", "EVS wins", "Both hit", "Both miss"
5. Export full results as CSV

---

## Key Changes (Sprint 12 → Sprint 13)

- **User authentication** — `PlatformUser` nodes in Neo4j with hashed passwords. Login gate on app startup. Chat histories scoped per user.
- **Chat deletion** — Delete individual chat sessions from the history panel.
- **Benchmark page** — Frederick vs EVS accuracy comparison with upload, metrics, filtering, and CSV export.
- **Ollama model discovery** — Sidebar queries `localhost:11434/api/tags` for installed models. Dropdown selectors replace manual text input.
- **Ollama setup script** — `ollama_setup.sh` automates first-time Ollama configuration on Anvil.
- **`stop` param fix** — Removed duplicate `stop` tokens from `OllamaLLM` constructor in `llm_agent_4o.py` that conflicted with LangChain's agent.
