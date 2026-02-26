"""
backend_client.py — Connection layer between Streamlit app and ncit-semantic-mapper / Neo4j.

Provides a single `BackendClient` class that:
  1. Connects directly to Neo4j (same credentials as kg_toolkit)
  2. Wraps exact_match, synonym_tool, semantic_retrievers
  3. Optionally initialises the LangChain agent for chat
  4. Falls back to mock data when Neo4j / Ollama are unreachable

Usage in app.py:
    from backend_client import get_client
    client = get_client()           # cached singleton
    client.exact_match_by_term("Lung Carcinoma")
"""

import os
import sys
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # reads .env in project root or cwd


# ──────────────────────────────────────────────
# Lightweight result containers
# ──────────────────────────────────────────────
@dataclass
class MatchResult:
    code: str = ""
    term: str = ""
    definition: str = ""
    node_type: str = ""
    score: float = 0.0
    source: str = ""          # "exact" | "synonym" | "semantic" | "fuzzy"
    extra: dict = field(default_factory=dict)


@dataclass
class GraphPayload:
    """Mirrors the shape the Streamlit graph page expects."""
    nodes: list = field(default_factory=list)   # [{"name":…, "type":…, "color":…}, …]
    edges: list = field(default_factory=list)    # [{"source":…, "target":…, "similarity":…}, …]


# ──────────────────────────────────────────────
# Backend Client
# ──────────────────────────────────────────────
class BackendClient:
    """
    Single entry-point for all Neo4j / kg_toolkit operations.
    Falls back to mock data when the database is unreachable.
    """

    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", "")
        self.neo4j_pass = os.getenv("NEO4J_PASSWORD", "")

        self._driver = None
        self._matcher = None          # get_node_match instance
        self._synonyms = None         # get_synonyms instance
        self._searcher = None         # SemanticSearcher instance
        self._agent = None            # LangChain agent executor
        self._agent_prompt = None

        self.connected = False
        self.agent_ready = False
        self.error: Optional[str] = None

        # Attempt connection
        self._connect()

    # ── Connection ────────────────────────────
    def _connect(self):
        """Try to connect to Neo4j and instantiate kg_toolkit classes."""
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_pass]):
            self.error = "Neo4j credentials missing. Set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env"
            return

        # Try importing kg_toolkit (ncit-semantic-mapper must be on sys.path)
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_pass),
            )
            # Quick connectivity check
            with self._driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
        except Exception as e:
            self.error = f"Neo4j connection failed: {e}"
            return

        # Instantiate toolkit classes (they each open their own driver — fine for now)
        try:
            from kg_toolkit.exact_match import get_node_match
            self._matcher = get_node_match(
                uri=self.neo4j_uri, username=self.neo4j_user, password=self.neo4j_pass
            )
        except Exception as e:
            print(f"[BackendClient] exact_match init failed: {e}")

        try:
            from kg_toolkit.synonym_tool import get_synonyms
            self._synonyms = get_synonyms(
                uri=self.neo4j_uri, username=self.neo4j_user, password=self.neo4j_pass
            )
        except Exception as e:
            print(f"[BackendClient] synonym_tool init failed: {e}")

        try:
            from kg_toolkit.semantic_retrievers import SemanticSearcher
            self._searcher = SemanticSearcher(
                uri=self.neo4j_uri, username=self.neo4j_user, password=self.neo4j_pass
            )
        except Exception as e:
            print(f"[BackendClient] SemanticSearcher init failed (Ollama may be down): {e}")

    # ── Agent (lazy init — expensive) ────────
    def init_agent(self) -> bool:
        """Initialise the LangChain ReAct agent. Call explicitly from UI."""
        if self.agent_ready:
            return True
        try:
            from kg_toolkit.llm_agent_4o import create_fresh_agent
            self._agent, self._agent_prompt = create_fresh_agent()
            self.agent_ready = True
            return True
        except Exception as e:
            self.error = f"Agent init failed: {e}"
            return False

    # ── Exact Match ──────────────────────────
    def exact_match_by_code(self, code: str) -> Optional[MatchResult]:
        if not self._matcher:
            return None
        try:
            r = self._matcher.get_exact_match_from_code(code.strip().upper())
            if not r:
                return None
            return MatchResult(
                code=r.get("code", code),
                term=r.get("term", ""),
                definition=r.get("definition", ""),
                node_type=r.get("type", ""),
                score=1.0,
                source="exact",
            )
        except Exception as e:
            print(f"[exact_match_by_code] {e}")
            return None

    def exact_match_by_term(self, term: str) -> Optional[MatchResult]:
        if not self._matcher:
            return None
        try:
            r = self._matcher.get_exact_match_from_term(term.strip())
            if not r:
                return None
            return MatchResult(
                code=r.get("code", ""),
                term=r.get("term", term),
                definition=r.get("definition", ""),
                node_type=r.get("type", ""),
                score=1.0,
                source="exact",
            )
        except Exception as e:
            print(f"[exact_match_by_term] {e}")
            return None

    def fuzzy_match(self, term: str, limit: int = 5) -> list[MatchResult]:
        if not self._matcher:
            return []
        try:
            rows = self._matcher.get_fuzzy_term_matches(term.strip(), limit=limit)
            return [
                MatchResult(
                    code=r.get("code", ""),
                    term=r.get("term", ""),
                    definition=r.get("definition", ""),
                    node_type=r.get("type", ""),
                    score=r.get("score", 0),
                    source="fuzzy",
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[fuzzy_match] {e}")
            return []

    # ── Synonyms ─────────────────────────────
    def synonyms_by_term(self, pv_term: str) -> list[str]:
        if not self._synonyms:
            return []
        try:
            return self._synonyms.get_synonyms_from_pv(pv_term.strip())
        except Exception as e:
            print(f"[synonyms_by_term] {e}")
            return []

    def synonyms_by_code(self, code: str) -> list[str]:
        if not self._synonyms:
            return []
        try:
            return self._synonyms.get_synonyms_from_termcode(code.strip().upper())
        except Exception as e:
            print(f"[synonyms_by_code] {e}")
            return []

    # ── Semantic Search ──────────────────────
    def semantic_search_pv(self, term: str, top_k: int = 5) -> list[MatchResult]:
        """Semantic search through PV → CDE path."""
        if not self._searcher:
            return []
        try:
            rows = self._searcher.find_cde_from_pv_term(term.strip(), top_k=top_k)
            return [
                MatchResult(
                    code=r.get("metadata", {}).get("pv_code", ""),
                    term=r.get("metadata", {}).get("pv_term", ""),
                    definition=r.get("text", ""),
                    score=r.get("score", 0),
                    source="semantic_pv",
                    extra={
                        "cde_code": r.get("metadata", {}).get("cde", ""),
                        "cde_term": r.get("metadata", {}).get("cde_term", ""),
                    },
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[semantic_search_pv] {e}")
            return []

    def semantic_search_ncit(self, term: str, top_k: int = 5) -> list[MatchResult]:
        """Semantic search through NCIT concept vector index."""
        if not self._searcher:
            return []
        try:
            rows = self._searcher.find_cde_from_ncit_term(term.strip(), top_k=top_k)
            return [
                MatchResult(
                    code=r.get("metadata", {}).get("concept_code", ""),
                    term=r.get("metadata", {}).get("concept_term", ""),
                    definition=r.get("text", ""),
                    score=r.get("score", 0),
                    source="semantic_ncit",
                    extra={
                        "pv_code": r.get("metadata", {}).get("pv_code", ""),
                        "pv_term": r.get("metadata", {}).get("pv_term", ""),
                        "cdes": r.get("metadata", {}).get("of_cdes", []),
                    },
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[semantic_search_ncit] {e}")
            return []

    def semantic_search_cde_definition(self, description: str, top_k: int = 5) -> list[MatchResult]:
        if not self._searcher:
            return []
        try:
            rows = self._searcher.find_cde_by_definition_similarity(description.strip(), top_k=top_k)
            return [
                MatchResult(
                    code=r.get("metadata", {}).get("cde_code", ""),
                    term=r.get("metadata", {}).get("cde_term", ""),
                    definition=r.get("metadata", {}).get("cde_definition", ""),
                    score=r.get("score", 0),
                    source="semantic_cde_defn",
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[semantic_search_cde_definition] {e}")
            return []

    def semantic_search_ncit_definition(self, description: str, top_k: int = 5) -> list[MatchResult]:
        if not self._searcher:
            return []
        try:
            rows = self._searcher.find_ncit_by_definition_similarity(description.strip(), top_k=top_k)
            return [
                MatchResult(
                    code=r.get("metadata", {}).get("concept_code", ""),
                    term=r.get("metadata", {}).get("concept_term", ""),
                    definition=r.get("metadata", {}).get("concept_definition", ""),
                    score=r.get("score", 0),
                    source="semantic_ncit_defn",
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[semantic_search_ncit_definition] {e}")
            return []

    # ── Context-aware reranked search ────────
    def contextaware_cde_from_pv(self, pv_term: str, top_k: int = 5) -> list[MatchResult]:
        if not self._searcher:
            return []
        try:
            rows = self._searcher.contextaware_cde_from_pv(pv_term.strip(), top_k=top_k)
            return [
                MatchResult(
                    code=r.get("metadata", {}).get("pv_code", ""),
                    term=r.get("metadata", {}).get("pv_term", ""),
                    definition=r.get("text", ""),
                    score=r.get("metadata", {}).get("combined_score", r.get("score", 0)),
                    source="semantic_pv_reranked",
                    extra={
                        "cde_code": r.get("metadata", {}).get("cde", ""),
                        "cde_term": r.get("metadata", {}).get("cde_term", ""),
                        "oc_term": r.get("metadata", {}).get("oc_term", ""),
                        "raw_score": r.get("metadata", {}).get("score", 0),
                    },
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[contextaware_cde_from_pv] {e}")
            return []

    # ── Agent Chat ───────────────────────────
    def agent_query(self, raw_value: str) -> str:
        """Run the LangChain ReAct agent on a raw medical value."""
        if not self.agent_ready or not self._agent:
            return "Agent not initialised. Click 'Initialise Agent' in the sidebar."
        try:
            from kg_toolkit.llm_agent_4o import map_raw_data_isolated
            return map_raw_data_isolated(self._agent, self._agent_prompt, raw_value)
        except Exception as e:
            return f"Agent error: {e}"

    # ── Graph data from Neo4j ────────────────
    def fetch_graph_neighbourhood(self, center_term: str = "", limit: int = 50) -> GraphPayload:
        """
        Pull real nodes + edges from Neo4j for the Graph Visualization page.
        If center_term is given, starts from that node; otherwise random sample.
        """
        if not self._driver:
            return GraphPayload()

        type_colors = {
            "NCIT": "#4fc3f7", "PV": "#4caf50", "CDE": "#ff9800",
            "SYN": "#9c27b0", "VDM": "#e91e63", "Term": "#607d8b",
        }

        try:
            with self._driver.session() as session:
                if center_term.strip():
                    # Neighbourhood query around a term
                    cypher = """
                     MATCH (start)
                    WHERE toLower(start.term) CONTAINS toLower($term) OR start.code = $term
                    WITH start LIMIT 1
                    
                    CALL {
                        WITH start
                        OPTIONAL MATCH path = (start)-[*1..2]-(neighbor)
                        RETURN path
                        LIMIT $limit
                    }
                    
                    WITH start, collect(path) AS paths
                    
                    UNWIND paths AS p
                    UNWIND relationships(p) AS r
                    WITH start, collect(DISTINCT r) AS distinctRels
                    
                    WITH distinctRels, 
                         collect(DISTINCT startNode(r)) + collect(DISTINCT endNode(r)) + [start] AS allNodes
                    
                    UNWIND allNodes AS n
                    WITH distinctRels, collect(DISTINCT n) AS uniqueNodes
                    
                    RETURN 
                        [n IN uniqueNodes | {
                            name: COALESCE(n.term, n.code, elementId(n)),
                            type: head(labels(n)),
                            code: n.code
                        }] AS nodes,
                        [r IN distinctRels | {
                            source: COALESCE(startNode(r).term, startNode(r).code, elementId(startNode(r))),
                            target: COALESCE(endNode(r).term, endNode(r).code, elementId(endNode(r))),
                            rel_type: type(r)
                        }] AS edges
                        """
                    result = session.run(cypher, term=center_term, limit=limit).single()
                else:
                    # Random sample of connected nodes
                    cypher = """
                    MATCH (a)-[r]->(b)
                    WITH a, r, b LIMIT $limit
                    WITH collect(DISTINCT a) + collect(DISTINCT b) AS allNodes,
                         collect({source: COALESCE(a.term, a.code, toString(id(a))),
                                  target: COALESCE(b.term, b.code, toString(id(b))),
                                  rel_type: type(r)}) AS edges
                    RETURN
                        [n IN allNodes | {name: COALESCE(n.term, n.code, toString(id(n))),
                                           type: head(labels(n)),
                                           code: n.code}] AS nodes,
                        edges
                    """
                    result = session.run(cypher, limit=limit).single()

                if not result:
                    return GraphPayload()

                raw_nodes = result["nodes"]
                raw_edges = result["edges"]

                nodes = [
                    {
                        "name": n["name"],
                        "type": n.get("type", "Unknown"),
                        "color": type_colors.get(n.get("type", ""), "#607d8b"),
                        "code": n.get("code", ""),
                    }
                    for n in raw_nodes if n["name"]
                ]
                edges = [
                    {
                        "source": e["source"],
                        "target": e["target"],
                        "similarity": 0.5,  # real similarity would come from embeddings
                        "rel_type": e.get("rel_type", "RELATED"),
                    }
                    for e in raw_edges if e.get("source") and e.get("target") and e.get("rel_type")
                ]

                return GraphPayload(nodes=nodes, edges=edges)

        except Exception as e:
            print(f"[fetch_graph_neighbourhood] {e}")
            return GraphPayload()

    # ── Raw Cypher ───────────────────────────
    def run_cypher(self, query: str, params: dict = None) -> list[dict]:
        """Execute an arbitrary read-only Cypher query."""
        if not self._driver:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(query, **(params or {}))
                return [record.data() for record in result]
        except Exception as e:
            print(f"[run_cypher] {e}")
            return []

    # ── NL-to-Cypher via Ollama ─────────────
    _ollama_llm = None          # cached LLM instance
    _ollama_available = None    # tri-state: None = untested, True/False

    GRAPH_SCHEMA_PROMPT = """You are a Neo4j Cypher query generator for a biomedical knowledge graph.
Given a natural language question, generate ONLY a valid Cypher query — no explanation, no markdown fences.

Graph schema
─────────────
Node labels (all also carry :Term):
  CDE  – Common Data Element  (code, term, definition)
  DEC  – Data Element Concept (code, term)
  NCIT – NCI Thesaurus Concept (code, term, definition, type)
  OC   – Object Class          (code, term)
  PR   – Property / Attribute  (code, term)
  PV   – Permissible Value     (code, term, definition)
  VDM  – Value Domain          (code, term)
  SYN  – Synonym               (term)

Relationships:
  (CDE)-[:HAS_VDM]->(VDM)
  (VDM)-[:HAS_PV]->(PV)
  (PV)-[:HAS_CONCEPT]->(NCIT)
  (NCIT)-[:HAS_SYNONYM]->(SYN)
  (CDE)-[:HAS_DEC]->(DEC)
  (DEC)-[:HAS_OC]->(OC)
  (DEC)-[:HAS_PR]->(PR)

Rules:
- Always LIMIT results (default 25) unless counting.
- Use toLower() for case-insensitive text matching.
- Return properties (code, term, definition), not raw nodes.
- Codes look like C1234 for NCIT; numeric strings for CDEs.

Examples:
  Q: How many synonyms for C1234?
  A: MATCH (n:NCIT {code:'C1234'})-[:HAS_SYNONYM]->(s:SYN) RETURN n.term AS concept, count(s) AS synonym_count

  Q: Show synonyms for 'Lung Carcinoma'
  A: MATCH (n:NCIT) WHERE toLower(n.term) CONTAINS 'lung carcinoma' WITH n LIMIT 1 MATCH (n)-[:HAS_SYNONYM]->(s:SYN) RETURN n.code AS code, n.term AS concept, s.term AS synonym LIMIT 25

  Q: What CDEs use concept C4878?
  A: MATCH (ncit:NCIT {code:'C4878'})<-[:HAS_CONCEPT]-(pv:PV)<-[:HAS_PV]-(vdm:VDM)<-[:HAS_VDM]-(cde:CDE) RETURN cde.code AS cde_code, cde.term AS cde_term, pv.term AS pv_term LIMIT 25
"""

    def _get_ollama(self):
        """Lazy-load and cache the Ollama LLM. Returns None if unavailable."""
        if self._ollama_available is False:
            return None
        if self._ollama_llm is not None:
            return self._ollama_llm
        try:
            from langchain_ollama import OllamaLLM
            llm = OllamaLLM(model="llama3.1-64", temperature=0)
            # Quick smoke test
            llm.invoke("RETURN 1")
            BackendClient._ollama_llm = llm
            BackendClient._ollama_available = True
            print("[BackendClient] Ollama LLM connected ✅")
            return llm
        except Exception as e:
            BackendClient._ollama_available = False
            print(f"[BackendClient] Ollama unavailable: {e}")
            return None

    @property
    def ollama_ready(self) -> bool:
        return self._ollama_available is True or (self._ollama_available is None and self._get_ollama() is not None)

    def nl_to_cypher(self, question: str, system_prompt: str = None) -> dict:
        """
        Convert a natural-language question to Cypher via Ollama,
        execute it on Neo4j, and return everything the UI needs.

        Returns: {
            "question": str,
            "cypher": str,
            "method": "ollama" | "pattern",
            "results": list[dict],
            "error": str | None,
        }
        """
        import re as _re

        prompt = system_prompt or self.GRAPH_SCHEMA_PROMPT
        cypher = None
        method = "pattern"

        # ── 1. Try Ollama ──────────────────────
        llm = self._get_ollama()
        if llm is not None:
            try:
                raw = llm.invoke(
                    f"{prompt}\n\nQuestion: {question}\nCypher:"
                ).strip()
                # Strip markdown fences if LLM wraps them
                cleaned = raw
                if "```" in cleaned:
                    for block in cleaned.split("```"):
                        b = block.strip()
                        if b.lower().startswith("cypher"):
                            b = b[6:].strip()
                        if b.upper().startswith(("MATCH", "CALL", "WITH", "RETURN", "OPTIONAL", "UNWIND")):
                            cleaned = b
                            break
                # Basic sanity: must contain RETURN
                if "RETURN" in cleaned.upper():
                    cypher = cleaned
                    method = "ollama"
            except Exception as e:
                print(f"[nl_to_cypher] Ollama call failed: {e}")

        # ── 2. Pattern-based fallback ──────────
        if cypher is None:
            cypher = self._pattern_cypher(question)
            method = "pattern"

        # ── 3. Execute on Neo4j ────────────────
        results = []
        error = None
        if self._driver:
            try:
                with self._driver.session() as session:
                    records = session.run(cypher)
                    results = [r.data() for r in records]
            except Exception as e:
                error = f"Cypher execution failed: {e}"
        else:
            error = "Neo4j not connected — query generated but not executed"

        return {
            "question": question,
            "cypher": cypher,
            "method": method,
            "results": results,
            "total": len(results),
            "error": error,
        }

    # ── Pattern-based Cypher generator (fallback) ──
    @staticmethod
    def _pattern_cypher(question: str) -> str:
        import re as _re
        q = question.lower()

        code_match = _re.search(r'\b(C\d{3,7})\b', question, _re.IGNORECASE)
        code = code_match.group(1).upper() if code_match else None

        if code and ("synonym" in q or "synonyms" in q):
            if "how many" in q or "count" in q:
                return f"MATCH (n:NCIT {{code: '{code}'}})-[:HAS_SYNONYM]->(syn:SYN) RETURN n.term as concept_term, count(syn) as synonym_count"
            return f"MATCH (n:NCIT {{code: '{code}'}})-[:HAS_SYNONYM]->(syn:SYN) RETURN n.term as concept_term, n.code as concept_code, syn.term as synonym LIMIT 25"

        if code:
            if "cde" in q or "data element" in q:
                return f"MATCH (ncit:NCIT {{code: '{code}'}})<-[:HAS_CONCEPT]-(pv:PV)<-[:HAS_PV]-(vdm:VDM)<-[:HAS_VDM]-(cde:CDE) RETURN cde.code as cde_code, cde.term as cde_term, pv.term as pv_term LIMIT 25"
            if "permissible" in q or "pv" in q:
                return f"MATCH (ncit:NCIT {{code: '{code}'}})<-[:HAS_CONCEPT]-(pv:PV) RETURN pv.code as pv_code, pv.term as pv_term, ncit.term as concept_term LIMIT 25"
            return f"MATCH (n:NCIT {{code: '{code}'}}) OPTIONAL MATCH (n)-[:HAS_SYNONYM]->(syn:SYN) RETURN n.code as code, n.term as term, n.definition as definition, collect(syn.term) as synonyms LIMIT 1"

        quoted = _re.findall(r"[\"']([^\"']+)[\"']", question)
        search_term = quoted[0] if quoted else None
        if not search_term:
            for pat in [r"related to (.+?)[\?\.\!]", r"about (.+?)[\?\.\!]",
                        r"for (.+?)[\?\.\!]", r"of (.+?)[\?\.\!]",
                        r"related to (.+)$", r"about (.+)$",
                        r"for (.+)$", r"of (.+)$"]:
                m = _re.search(pat, q)
                if m:
                    search_term = m.group(1).strip()
                    break

        if search_term:
            if "synonym" in q:
                return f"MATCH (ncit:NCIT) WHERE toLower(ncit.term) CONTAINS toLower('{search_term}') WITH ncit LIMIT 5 MATCH (ncit)-[:HAS_SYNONYM]->(syn:SYN) RETURN ncit.code as code, ncit.term as concept, syn.term as synonym LIMIT 25"
            if "cde" in q or "data element" in q:
                return f"MATCH (ncit:NCIT) WHERE toLower(ncit.term) CONTAINS toLower('{search_term}') WITH ncit LIMIT 3 MATCH (ncit)<-[:HAS_CONCEPT]-(pv:PV)<-[:HAS_PV]-(vdm:VDM)<-[:HAS_VDM]-(cde:CDE) RETURN cde.code as cde_code, cde.term as cde_term, ncit.term as concept LIMIT 25"
            return f"MATCH (n:NCIT) WHERE toLower(n.term) CONTAINS toLower('{search_term}') RETURN n.code as code, n.term as term, n.definition as definition, n.type as type ORDER BY n.term LIMIT 25"

        return "MATCH (n:NCIT) RETURN n.code as code, n.term as term, n.type as type LIMIT 25"

    # ── Cleanup ──────────────────────────────
    def close(self):
        for obj in [self._matcher, self._synonyms, self._searcher]:
            if obj and hasattr(obj, "close"):
                try:
                    obj.close()
                except Exception:
                    pass
        if self._driver:
            try:
                self._driver.close()
            except Exception:
                pass

    # ── Status ───────────────────────────────
    def status_dict(self) -> dict:
        return {
            "neo4j_connected": self.connected,
            "exact_match_ready": self._matcher is not None,
            "synonym_ready": self._synonyms is not None,
            "semantic_ready": self._searcher is not None,
            "agent_ready": self.agent_ready,
            "ollama_ready": self._ollama_available is True,
            "error": self.error,
        }


# ──────────────────────────────────────────────
# Singleton accessor (use from Streamlit via st.cache_resource)
# ──────────────────────────────────────────────
_client_instance: Optional[BackendClient] = None


def get_client() -> BackendClient:
    """Return a module-level singleton BackendClient."""
    global _client_instance
    if _client_instance is None:
        _client_instance = BackendClient()
    return _client_instance
