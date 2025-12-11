# Frederick Platform — File → Backend Integration & Frontend

This update enables the **frontend (Streamlit)** to send uploaded term files to a backend API for processing (e.g., sorting or clustering medical terms).

---

## Components

| File | Description |
|------|--------------|
| `streamlitog.py` | Main Streamlit frontend file (modified) |
| `mock_backend.py` | FastAPI mock backend for local testing |
| `mock_xxx.txt` | Sample input file containing comma-separated terms |

---

## Setup Instructions
### 1️Install Dependencies
```bash
pip install streamlit fastapi uvicorn requests

```

# Neo4j Knowledge Graph Frontend

A web-based dashboard for exploring, querying, and managing a Neo4j-backed medical terminology graph. This frontend provides:

- An interactive **knowledge graph viewer** for term mapping
- A **graph-aware RAG chatbot** that answers questions using indexed data and graph context
- A **document upload & embedding interface** for powering semantic search and downstream models

It is designed to work with the Neo4j Knowledge Graph Toolkit and related SI-Tamer tooling for semantic mapping of caDSR and NCIt terminology. :contentReference[oaicite:0]{index=0}  

---

## Overview

Researchers and analysts often work with heterogeneous medical data coming from multiple repositories (caDSR, NCIt, etc.), each using its own terminology and coding standards. This frontend provides a unified, analyst-friendly interface to:

- Visualize how terms are connected in a Neo4j graph
- Upload new documents to be embedded and indexed for semantic search
- Ask natural-language questions over the indexed data and the current graph context

The goal is to make semantic mapping, term exploration, and graph-aware reasoning accessible without requiring users to write queries or directly interact with Neo4j.

---

## Related Project

This frontend is a companion to the **Neo4j Knowledge Graph Toolkit**, a Python toolkit that handles semantic mapping, exact/synonym matching, and LLM-based reasoning over NCIt and caDSR terminology. :contentReference[oaicite:1]{index=1}  

Together, the toolkit and this UI form an end-to-end stack for:

1. Building and querying a terminology knowledge graph in Neo4j
2. Surfacing graph insights and LLM-generated responses in an interactive web interface

---

## Key Features

### 1. Knowledge Graph Visualization (Neo4j Term Mapping)

A dedicated **Graph Visualization** view for exploring the terminology graph.

- Load and render nodes and edges from the backend Neo4j graph
- Filter by node type (e.g., NCIT, PV, SYN, CDE, etc.)
- Control graph **depth** and **maximum node count** from the UI
- Select layout mode (e.g., force-directed) for better visual exploration
- Quickly see a snapshot of graph size (node/edge counts) and load status

This view provides the main workspace for inspecting how terms, permissible values, and codes map to each other and to standardized NCIt concepts.

---

### 2. Document Embedding Upload

An **Upload** page for supplying new documents to be embedded and indexed.

- Drag-and-drop area for uploading training and reference documents
- Supports multiple file types (e.g., CSV, JSON, TXT, PDF, XLSX – subject to backend configuration)
- Configurable options, such as:
  - **Upload Type** (e.g., training data, term parsing)
  - **Target Model** (e.g., specific RAG model version)
  - **Preprocessing** mode (e.g., auto-detect)
- A **Recent Training Jobs** table showing:
  - Job ID
  - Model used
  - Number of files
  - Job status (Completed / Running / Failed)
  - Accuracy (if available)
  - Duration

This feature closes the loop between raw documents and indexable semantic representations, enabling richer retrieval and better RAG performance.

---

### 3. Graph-Aware RAG Chatbot

A **Graph AI Assistant** for conversational querying of the knowledge graph and indexed documents.

- Accepts natural-language questions from the user
- Leverages the RAG backend and graph context to generate responses
- Can surface:
  - Related terms and diseases (e.g., terms most relevant to a condition such as leukemia)
  - Explanations grounded in graph relationships
  - Contextual suggestions based on surrounding nodes
- Displays node and edge counts for the current graph context so users understand the scope of the answer

By combining embeddings, Neo4j graph structure, and LLM reasoning, the chatbot helps users explore the terminology space without writing Cypher queries.

---

## UI Layout

The application follows a dashboard-style layout:

- **Left Sidebar Navigation**
  - Dashboard
  - AI Chat
  - Graph Visualization
  - Metrics
  - File Upload
  - Settings
  - Export Data
- **Main Content Area**
  - Renders the active module (Graph, Upload, Chat, etc.)
- **Quick Stats Panel**
  - Displays high-level metrics such as active users, total documents, and relative changes

This layout is intended to be intuitive for analysts who regularly move between graph exploration, document management, and conversational querying.

---

## Technology Stack

The frontend is implemented as a modern single-page application, using:

- **Streamlit** 

---
