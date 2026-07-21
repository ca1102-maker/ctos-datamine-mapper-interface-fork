# 🧬 FNL Mapper

Medical terminology mapping platform built on **Neo4j**, **Streamlit**, and **LangChain**.
Maps raw clinical data terms to standardized NCIT/caDSR terminology via exact, fuzzy, synonym, and semantic search — with a built-in LLM agent for conversational querying.

---

## Features

- **User Authentication** — Per-user accounts stored as `PlatformUser` nodes in Neo4j. Login/signup on startup; chat histories are scoped to each user via `(PlatformUser)-[:OWNS]->(ChatSession)`.
- **AI Chat (Home)** — Conversational interface with smart routing: OpenAI/Anthropic agent → mock fallback. Chat sessions persist in Neo4j with full message history. Supports creating, loading, and deleting chats.
- **Map & Grade** — Batch CSV/TSV upload for mapping raw terms to NCIT/caDSR. Includes an integrated data cleaning step (whitespace stripping, quote removal, datetime row removal, duplicate deduplication, and dual ICD-O code splitting) before mapping. Table-view results with inline SME grading and selective export.
- **Explore Graph** — Natural language → Cypher query generation powered by user-selected OpenAI or Anthropic model. Interactive knowledge graph visualization.
- **Benchmark** — Upload EVS ground-truth files and compare Frederick's search cascade accuracy (exact → fuzzy → synonym → semantic) against EVS baseline. Exportable results with filtering.
- **Dashboard** — KPI overview and system metrics.
- **Ingest Data** — Upload EVS result files (.tsv) directly into Neo4j.
- **Settings** — Connection info, system prompt editor, preferences.
- **User-Supplied API Keys** — User provides OpenAI and/or Anthropic keys via sidebar after login. Available models update dynamically based on keys provided. Dropdown selection for reasoning agent and cypher generation model. Note: Semantic search requires OpenAI key (text-embedding-ada-002) regardless of selected chat model.

---

## Project Structure

```
frederick/
├── app/
│   ├── main.py                  # Streamlit entrypoint, auth gate, router
│   ├── styles.py                # Shared CSS
│   ├── components/
│   │   └── sidebar.py           # Status, OpenAI/Anthropic model picker, API key inputs, nav, logout
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
│       ├── neo4j_client.py      # BackendClient (Neo4j, kg_toolkit, auth, chat, multi-provider LLM routing)
│       └── models.py            # MatchResult, GraphPayload dataclasses
├── assets/
│   ├── icon.png
│   └── logo.png
├── config/
│   └── eg.env                   # Example environment variables
├── ncit-semantic-mapper/        # kg_toolkit library (exact match, fuzzy, synonym, semantic search, LLM agent)
├── si-tamer/                    # si_tamer library 
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
- Access to the Neo4j instance 
- An OpenAI API key (required for semantic search and GPT models)
- Anthropic API key (Optional, for Claude models)

### 1. Clone & enter

```bash
git clone <repo-url>
cd ctos-datamine-mapper-interface-fork
```

### 2. Set up environment variables

```bash
cp config/eg.env .env
# Edit .env with your credentials:
#   NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
```

### 3. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the app

```bash
chmod +x run.sh
./run.sh
```
The app opens at http://localhost:8501. Create an account to get started.
---

### 6. Enter your API keys

After logging in, enter your API keys in the sidebar:

- **OpenAI API key** — required for semantic search and GPT models. Get one at platform.openai.com
- Anthropic API key — optional, for Claude models. Get one at console.anthropic.com


## LLM Routing

The platform uses a two-tier fallback for chat responses:

1. **OpenAI or Anthropic agent (user-supplied)** (remote) — Uses the model selected in the sidebar. Full tool-calling agent with access to exact match, synonym, fuzzy, and semantic search tools. Requires the user to provide their own API key in the sidebar.
2. **Mock response** — Placeholder when no API Key is provided or agent is unavailable.

The sidebar dynamically populates available models based on API keys entered:

- **OpenAI Key** → enables gpt-4o, gpt-4o-mini, gpt-4-turbo
- **Anthropic Key** → enables claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5
- **Both keys** → all models available

**Note**: Semantic search always requires an OpenAI API key regardless of the selected chat model, as the knowledge graph vectors were pre-computed using text-embedding-ada-002. 

---

## Benchmark

The Benchmark page (`🏆 Benchmark` in sidebar) compares Frederick's mapping accuracy against EVS ground truth:

1. Upload a CDA/EVS summary TSV file
2. Frederick runs its search cascade (exact → fuzzy → synonym → semantic) on each term
3. Results show #1 hit rate, top-K hit rate, and head-to-head comparison vs EVS
4. Filter by "Frederick wins", "EVS wins", "Both hit", "Both miss"
5. Export full results as CSV

---

## Recent Changes

- **Multi-provider LLM support** — Replaced Ollama with OpenAI and Anthropic as LLM providers. Users supply their own API keys via the sidebar after login. Available models update dynamically based on which keys are provided.
- **User-supplied API keys** — Sidebar now includes password-input fields for OpenAI and Anthropic API keys. Keys are stored in session state for the duration of the session and cleared on logout.
- **Dynamic model selection** — Unified model dropdown replaces Ollama model discovery. OpenAI models (gpt-4o, gpt-4o-mini, gpt-4-turbo) appear when an OpenAI key is provided; Anthropic models (claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5) appear when an Anthropic key is provided.
- **Multi-provider LLM routing** — neo4j_client.py and llm_agent_4o.py now detect the selected model and route to ChatOpenAI or ChatAnthropic accordingly. Cypher generation also supports both providers.
- **Semantic search embedding fix** — semantic_retrievers.py corrected to use text-embedding-ada-002 (matching the pre-computed vectors in Neo4j) instead of text-embedding-3-small. Semantic search now requires an OpenAI key regardless of the selected chat model.
- **Data cleaning step in Map & Grade** — Added an integrated pre-mapping cleaning component that strips whitespace, removes quotes, filters datetime rows, deduplicates entries, and splits dual ICD-O codes into separate rows. Cleaned data persists across reruns via session state with options to preview, apply, and reset.
- **Suggested chat prompts updated** — Home page prompts replaced with medical mapping queries that properly exercise the agent's tools.
- **LangGraph agent migration** — llm_agent_4o.py migrated from AgentExecutor + old LangChain create_react_agent to LangGraph's create_react_agent, compatible with LangChain 1.3.x.
- **Deployment** — App deployed on GCP VM at http://35.229.118.82:8501, accessible without SSH tunnel via GCP firewall rule allowing port 8501.
- **Removed Ollama dependency** — ollama_setup.sh removed from required setup steps. langchain-ollama removed from dependencies. langchain-anthropic added.
