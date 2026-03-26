# LLM-Based Mapping Tool for Biomedical Research Data

A specialized platform for harmonizing biomedical research terms with the **National Cancer Institute Thesaurus (NCIT)**. This tool uses a multi-layered approach—combining deterministic matching with LLM-driven semantic search—to map complex clinical data to standardized ontologies.

## 🚀 Overview

The system bridges the gap between raw biomedical datasets and standardized terminologies. By utilizing a **Neo4j graph database** and Large Language Models, it provides a high-precision mapping interface that understands the context and hierarchy of biomedical concepts.

## 🏗 Architecture & Components

The project is organized into several modular components:

*   **`app_wired.py`**: The main entry point. A **Streamlit** dashboard providing an interactive UI for researchers.
*   **`backend_client.py`**: The orchestration layer that connects the frontend to mapping services and the database.
*   **`ncit_semantic_mapper/`**: The core logic engine, featuring:
    *   **Exact Match**: Fast, string-perfect lookups.
    *   **Fuzzy Match**: Similarity-based matching to handle typos and minor variations.
    *   **Semantic Search**: Natural language search powered by **LLMs** and **Neo4j** graph embeddings.
*   **`si_tamer/`**: A specialized utility for normalizing SI units and numerical data within biomedical contexts.
*   **`frontend/` & `backend/`**: Modular directories for API development and extended UI components.

## 🛠 Features

- **Natural Language Mapping**: Search for terms using plain English; the LLM interprets intent and maps it to the closest NCIT concept.
- **Graph-Powered Context**: Leverages Neo4j to navigate the hierarchical relationships within the NCIT ontology.
- **Hybrid Search Pipeline**: Falls back from Exact → Fuzzy → Semantic to ensure the most accurate result is always found.
- **Streamlit Integration**: Real-time visualization of mapping results and similarity scores.

## 📦 Getting Started

### Prerequisites
- Python 3.9+
- Neo4j Database (populated with NCIT data)
- LLM API Key (OpenAI, Anthropic, or Local)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/TheDataMine/f2025_s2026_wl_fnl_userinterface

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt

## 🖥 Usage
Run the Streamlit application to start the mapping interface:  
    ```bash  
    streamlit run app_wired.py


## 📂 Project Structure

├── app_wired.py            # Streamlit Frontend  
├── backend_client.py       # Logic Orchestration  
├── ncit_semantic_mapper/   # Exact/Fuzzy/Semantic Match logic  
├── si_tamer/               # SI Unit normalization  
├── backend/                # API & Core Services  
└── frontend/               # UI Assets  



