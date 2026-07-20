"""
Neo4j + kg_toolkit connection layer.

Provides a single BackendClient class that:
  1. Connects directly to Neo4j
  2. Wraps exact_match, synonym_tool, semantic_retrievers from kg_toolkit
  3. Optionally initialises the LangChain agent for chat
  4. Falls back gracefully when Neo4j / Ollama are unreachable

Usage:
    from app.services.neo4j_client import get_client
    client = get_client()
    client.exact_match_by_term("Lung Carcinoma")
"""

import os
import sys
import json
import time
import hashlib
import uuid
import re as _re
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
import streamlit as st

from app.services.models import MatchResult, GraphPayload

load_dotenv()


class BackendClient:
    """Single entry-point for all Neo4j / kg_toolkit operations."""

    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", "")
        self.neo4j_pass = os.getenv("NEO4J_PASSWORD", "")

        self._driver = None
        self._matcher = None
        self._synonyms = None
        self._searcher = None
        self._agent = None
        self._agent_prompt = None

        self.connected = False
        self.agent_ready = False
        self.error: Optional[str] = None
        self.current_agent_model = None
        self.current_cypher_model = None

        self._connect()

    # ── Connection ────────────────────────────────────────────────────────

    def _connect(self):
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_pass]):
            self.error = "Neo4j credentials missing. Set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env"
            return

        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_pass),
            )
            with self._driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
        except Exception as e:
            self.error = f"Neo4j connection failed: {e}"
            return

        # kg_toolkit components (each may fail independently)
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
            print(f"[BackendClient] SemanticSearcher init failed: {e}")

    # ── Agent (lazy, expensive) ───────────────────────────────────────────

    def init_agent(self, model_name="llama3.1") -> bool:
        if self.agent_ready and self.current_agent_model == model_name:
            return True
        try:
            from kg_toolkit.llm_agent_4o import create_fresh_agent
            self._agent, self._agent_prompt = create_fresh_agent(model_name=model_name)
            self.agent_ready = True
            self.current_agent_model = model_name
            return True
        except Exception as e:
            self.error = f"Agent init failed: {e}"
            return False

    def agent_query(self, raw_value: str) -> str:
        if not self.agent_ready or not self._agent:
            return "Agent not initialised. Click 'Initialise Agent' in the sidebar."
        try:
            from kg_toolkit.llm_agent_4o import map_raw_data_isolated
            return map_raw_data_isolated(self._agent, self._agent_prompt, raw_value)
        except Exception as e:
            return f"Agent error: {e}"

    # ── Claude API (fallback when Ollama is down) ─────────────────────────

    _claude_available = None

    def query_claude(self, user_message: str, system_prompt: str = None) -> str:
        """Send a message to the Anthropic Claude API. Returns the response text."""
        api_key = st.session_state.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return "Claude API key not set. Please enter your Anthropic API key in the sidebar."
        try:
            import requests
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": st.session_state.get("agent_model", os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")),
                    "max_tokens": 1024,
                    "system": system_prompt or self.GRAPH_SCHEMA_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            BackendClient._claude_available = True
            return data["content"][0]["text"]
        except Exception as e:
            print(f"[query_claude] {e}")
            BackendClient._claude_available = False
            return f"Claude API error: {e}"

    @property
    def claude_ready(self) -> bool:
        return bool(st.session_state.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY"))

    def chat_query(self, user_message: str, system_prompt: str = None) -> str:
        """
        Smart routing: try agent (Ollama) first, fall back to Claude API,
        then fall back to mock response.
        """
        # 1. Try Ollama agent
        if self.agent_ready:
            try:
                result = self.agent_query(user_message)
                if result and "Agent not initialised" not in result and "Agent error" not in result:
                    return result
            except Exception as e:
                print(f"[chat_query] Ollama agent failed: {e}")
    
        # 2. Try Claude API
        if self.claude_ready:
            prompt = system_prompt or (
                "You are an expert medical data mapper specializing in NCIT terminology. "
                "Help map raw medical data values to standardized NCIT terms and codes. "
                "Be thorough but concise."
            )
            result = self.query_claude(user_message, system_prompt=prompt)
            if "Claude API error" not in result:
                return result
    
        # 3. Mock fallback
        short = user_message[:20]
        return (
            f"Based on the knowledge base, here's what I found:\n\n"
            f"**Relevant Documents:** 3 matches found\n\n"
            f"- **Document A** (95% relevance): Contains information about {short}...\n"
            f"- **Document B** (87% relevance): Related context on the topic\n"
            f"- **Document C** (76% relevance): Supporting information\n\n"
            f"*💡 Add ANTHROPIC_API_KEY to .env for live Claude answers, or fix the Ollama agent.*"
        )

    # ── Exact Match ───────────────────────────────────────────────────────

    def exact_match_by_code(self, code: str) -> Optional[MatchResult]:
        if not self._matcher:
            return None
        try:
            r = self._matcher.get_exact_match_from_code(code.strip().upper())
            if not r:
                return None
            return MatchResult(
                code=r.get("code", code), term=r.get("term", ""),
                definition=r.get("definition", ""), node_type=r.get("type", ""),
                score=1.0, source="exact",
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
                code=r.get("code", ""), term=r.get("term", term),
                definition=r.get("definition", ""), node_type=r.get("type", ""),
                score=1.0, source="exact",
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
                    code=r.get("code", ""), term=r.get("term", ""),
                    definition=r.get("definition", ""), node_type=r.get("type", ""),
                    score=r.get("score", 0), source="fuzzy",
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[fuzzy_match] {e}")
            return []

    # ── Synonyms ──────────────────────────────────────────────────────────

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

    # ── Semantic Search ───────────────────────────────────────────────────

    def semantic_search_pv(self, term: str, top_k: int = 5) -> list[MatchResult]:
        if not self._searcher:
            return []
        try:
            rows = self._searcher.find_cde_from_pv_term(term.strip(), top_k=top_k)
            return [
                MatchResult(
                    code=r.get("metadata", {}).get("pv_code", ""),
                    term=r.get("metadata", {}).get("pv_term", ""),
                    definition=r.get("text", ""),
                    score=r.get("score", 0), source="semantic_pv",
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
        if not self._searcher:
            return []
        try:
            rows = self._searcher.find_cde_from_ncit_term(term.strip(), top_k=top_k)
            return [
                MatchResult(
                    code=r.get("metadata", {}).get("concept_code", ""),
                    term=r.get("metadata", {}).get("concept_term", ""),
                    definition=r.get("text", ""),
                    score=r.get("score", 0), source="semantic_ncit",
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
                    score=r.get("score", 0), source="semantic_cde_defn",
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
                    score=r.get("score", 0), source="semantic_ncit_defn",
                )
                for r in rows
            ]
        except Exception as e:
            print(f"[semantic_search_ncit_definition] {e}")
            return []

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

    # ── Graph data ────────────────────────────────────────────────────────

    def fetch_graph_neighbourhood(self, center_term: str = "", limit: int = 50) -> GraphPayload:
        if not self._driver:
            return GraphPayload()

        type_colors = {
            "NCIT": "#4fc3f7", "PV": "#4caf50", "CDE": "#ff9800",
            "SYN": "#9c27b0", "VDM": "#e91e63", "Term": "#607d8b",
        }

        try:
            with self._driver.session() as session:
                if center_term.strip():
                    cypher = """
                    MATCH (start)
                    WHERE toLower(start.term) CONTAINS toLower($term) OR start.code = $term
                    WITH start LIMIT 1
                    CALL {
                        WITH start
                        OPTIONAL MATCH path = (start)-[*1..2]-(neighbor)
                        RETURN path LIMIT $limit
                    }
                    WITH start, collect(path) AS paths
                    UNWIND (CASE WHEN paths = [] THEN [null] ELSE paths END) AS p
                    UNWIND (CASE WHEN p IS NULL THEN [null] ELSE relationships(p) END) AS r
                    WITH start, collect(DISTINCT r) AS rawRels
                    WITH start, [rel IN rawRels WHERE rel IS NOT NULL] AS distinctRels
                    UNWIND (CASE WHEN distinctRels = [] THEN [null] ELSE distinctRels END) AS rel
                    WITH start, distinctRels,
                         collect(DISTINCT startNode(rel)) + collect(DISTINCT endNode(rel)) AS endpoints
                    UNWIND (endpoints + [start]) AS n
                    WITH distinctRels, collect(DISTINCT n) AS rawNodes
                    WITH distinctRels, [node IN rawNodes WHERE node IS NOT NULL] AS uniqueNodes
                    RETURN
                        [n IN uniqueNodes | {
                            name: COALESCE(n.term, n.code, toString(id(n))),
                            type: head(labels(n)),
                            code: n.code
                        }] AS nodes,
                        [rel IN distinctRels | {
                            source: COALESCE(startNode(rel).term, startNode(rel).code, toString(id(startNode(rel)))),
                            target: COALESCE(endNode(rel).term, endNode(rel).code, toString(id(endNode(rel)))),
                            rel_type: type(rel)
                        }] AS edges
                    """
                    result = session.run(cypher, term=center_term, limit=limit).single()
                else:
                    cypher = """
                    MATCH (a)-[r]->(b) WITH a, r, b LIMIT $limit
                    WITH collect(DISTINCT r) AS distinctRels
                    UNWIND distinctRels AS rel
                    WITH distinctRels, collect(DISTINCT startNode(rel)) + collect(DISTINCT endNode(rel)) AS endpoints
                    UNWIND endpoints AS n
                    WITH distinctRels, collect(DISTINCT n) AS uniqueNodes
                    RETURN
                        [n IN uniqueNodes | {
                            name: COALESCE(n.term, n.code, toString(id(n))),
                            type: head(labels(n)), code: n.code
                        }] AS nodes,
                        [rel IN distinctRels | {
                            source: COALESCE(startNode(rel).term, startNode(rel).code, toString(id(startNode(rel)))),
                            target: COALESCE(endNode(rel).term, endNode(rel).code, toString(id(endNode(rel)))),
                            rel_type: type(rel)
                        }] AS edges
                    """
                    result = session.run(cypher, limit=limit).single()

                if not result:
                    return GraphPayload()

                nodes = [
                    {"name": n["name"], "type": n.get("type", "Unknown"),
                     "color": type_colors.get(n.get("type", ""), "#607d8b"),
                     "code": n.get("code", "")}
                    for n in result["nodes"] if n["name"]
                ]
                edges = [
                    {"source": e["source"], "target": e["target"],
                     "similarity": 0.5, "rel_type": e.get("rel_type", "RELATED")}
                    for e in result["edges"]
                    if e.get("source") and e.get("target") and e.get("rel_type")
                ]
                return GraphPayload(nodes=nodes, edges=edges)

        except Exception as e:
            print(f"[fetch_graph_neighbourhood] {e}")
            return GraphPayload()

    # ── Raw Cypher ────────────────────────────────────────────────────────

    def run_cypher(self, query: str, params: dict = None) -> list[dict]:
        if not self._driver:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(query, **(params or {}))
                return [record.data() for record in result]
        except Exception as e:
            print(f"[run_cypher] {e}")
            return []

    def write_cypher(self, query: str, params: dict | None = None) -> dict:
        if not self._driver:
            return {"ok": False, "error": "Neo4j not connected"}
        try:
            with self._driver.session() as session:
                session.execute_write(lambda tx: tx.run(query, **(params or {})).consume())
            return {"ok": True, "error": None}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── User Authentication (Neo4j) ──────────────────────────────────────

    @staticmethod
    def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """Hash a password with a random salt. Returns (hash_hex, salt_hex)."""
        if salt is None:
            salt = uuid.uuid4().hex
        salted = (salt + password).encode("utf-8")
        hashed = hashlib.sha256(salted).hexdigest()
        return hashed, salt

    def create_user(self, username: str, password: str, display_name: str = "") -> dict:
        """Create a new PlatformUser node. Returns {ok, user_id, error}."""
        if not self._driver:
            return {"ok": False, "user_id": None, "error": "Neo4j not connected"}
        # Check for duplicate username
        existing = self.run_cypher(
            "MATCH (u:PlatformUser {username: $username}) RETURN u.user_id AS uid LIMIT 1",
            {"username": username.strip().lower()},
        )
        if existing:
            return {"ok": False, "user_id": None, "error": "Username already exists"}

        user_id = f"user:{uuid.uuid4().hex[:12]}"
        pw_hash, salt = self._hash_password(password)
        now = datetime.utcnow().isoformat()
        result = self.write_cypher(
            """CREATE (u:PlatformUser {
                user_id: $user_id, username: $username,
                display_name: $display_name,
                pw_hash: $pw_hash, pw_salt: $salt,
                created_at: $ts
            })""",
            {
                "user_id": user_id,
                "username": username.strip().lower(),
                "display_name": display_name.strip() or username.strip(),
                "pw_hash": pw_hash, "salt": salt, "ts": now,
            },
        )
        if result["ok"]:
            return {"ok": True, "user_id": user_id, "error": None}
        return {"ok": False, "user_id": None, "error": result["error"]}

    def authenticate_user(self, username: str, password: str) -> dict:
        """Verify credentials. Returns {ok, user_id, display_name, error}."""
        if not self._driver:
            return {"ok": False, "user_id": None, "display_name": None, "error": "Neo4j not connected"}
        rows = self.run_cypher(
            """MATCH (u:PlatformUser {username: $username})
            RETURN u.user_id AS user_id, u.display_name AS display_name,
                   u.pw_hash AS pw_hash, u.pw_salt AS pw_salt""",
            {"username": username.strip().lower()},
        )
        if not rows:
            return {"ok": False, "user_id": None, "display_name": None, "error": "User not found"}
        row = rows[0]
        candidate_hash, _ = self._hash_password(password, salt=row["pw_salt"])
        if candidate_hash != row["pw_hash"]:
            return {"ok": False, "user_id": None, "display_name": None, "error": "Incorrect password"}
        return {"ok": True, "user_id": row["user_id"], "display_name": row["display_name"], "error": None}

    # ── Chat History (Neo4j) ──────────────────────────────────────────────

    def create_chat_session(self, title: str = "New Chat", user_id: str = None) -> dict:
        if not self._driver:
            return {"ok": False, "chat_id": None, "error": "Neo4j not connected"}
        chat_id = f"chat:{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        if user_id:
            result = self.write_cypher(
                """MATCH (u:PlatformUser {user_id: $user_id})
                CREATE (c:ChatSession {
                    chat_id: $chat_id, title: $title,
                    created_at: $ts, updated_at: $ts
                })
                CREATE (u)-[:OWNS]->(c)""",
                {"user_id": user_id, "chat_id": chat_id, "title": title, "ts": now},
            )
        else:
            result = self.write_cypher(
                """CREATE (c:ChatSession {
                    chat_id: $chat_id, title: $title,
                    created_at: $ts, updated_at: $ts
                })""",
                {"chat_id": chat_id, "title": title, "ts": now},
            )
        return {"ok": result["ok"], "chat_id": chat_id if result["ok"] else None, "error": result["error"]}

    def update_chat_session_title(self, chat_id: str, title: str) -> dict:
        if not self._driver:
            return {"ok": False, "error": "Neo4j not connected"}
        return self.write_cypher(
            "MATCH (c:ChatSession {chat_id: $chat_id}) SET c.title = $title, c.updated_at = $ts",
            {"chat_id": chat_id, "title": title, "ts": datetime.utcnow().isoformat()},
        )

    def save_chat_message(self, chat_id: str, role: str, content: str, position: int) -> dict:
        if not self._driver:
            return {"ok": False, "message_id": None, "error": "Neo4j not connected"}
        message_id = f"msg:{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow().isoformat()
        result = self.write_cypher(
            """MATCH (c:ChatSession {chat_id: $chat_id})
            CREATE (m:ChatMessage {
                message_id: $message_id, chat_id: $chat_id,
                role: $role, content: $content,
                created_at: $ts, position: $position
            })
            CREATE (c)-[:HAS_MESSAGE]->(m)
            SET c.updated_at = $ts""",
            {"chat_id": chat_id, "message_id": message_id, "role": role,
             "content": content, "ts": now, "position": position},
        )
        return {"ok": result["ok"], "message_id": message_id if result["ok"] else None, "error": result["error"]}

    def list_chat_sessions(self, limit: int = 30, user_id: str = None) -> list[dict]:
        if user_id:
            return self.run_cypher(
                """MATCH (u:PlatformUser {user_id: $user_id})-[:OWNS]->(c:ChatSession)
                RETURN c.chat_id AS chat_id, c.title AS title,
                       c.created_at AS created_at, c.updated_at AS updated_at
                ORDER BY c.updated_at DESC LIMIT $limit""",
                {"user_id": user_id, "limit": limit},
            )
        return self.run_cypher(
            """MATCH (c:ChatSession)
            RETURN c.chat_id AS chat_id, c.title AS title,
                   c.created_at AS created_at, c.updated_at AS updated_at
            ORDER BY c.updated_at DESC LIMIT $limit""",
            {"limit": limit},
        )

    def load_chat_messages(self, chat_id: str) -> list[dict]:
        return self.run_cypher(
            """MATCH (c:ChatSession {chat_id: $chat_id})-[:HAS_MESSAGE]->(m:ChatMessage)
            RETURN m.role AS role, m.content AS content,
                   m.position AS position, m.created_at AS created_at
            ORDER BY m.position ASC, m.created_at ASC""",
            {"chat_id": chat_id},
        )

    def delete_chat_session(self, chat_id: str) -> dict:
        """Delete a ChatSession and all its ChatMessage nodes + relationships."""
        if not self._driver:
            return {"ok": False, "error": "Neo4j not connected"}
        return self.write_cypher(
            """MATCH (c:ChatSession {chat_id: $chat_id})
            OPTIONAL MATCH (c)-[:HAS_MESSAGE]->(m:ChatMessage)
            DETACH DELETE m, c""",
            {"chat_id": chat_id},
        )

    # ── NL-to-Cypher ──────────────────────────────────────────────────────

    _ollama_llm = None
    _ollama_available = None

    GRAPH_SCHEMA_PROMPT = """You are a Neo4j Cypher query generator for a biomedical knowledge graph.
Given a natural language question, generate ONLY a valid Cypher query — no explanation, no markdown fences, no conversational text.

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
- ALWAYS LIMIT results (default 25) unless counting.
- Use `toLower(n.term) CONTAINS toLower('string')` for case-insensitive matching.
- Nodes use `.term`, NEVER `.name`.
- Return properties (code, term, definition), not raw nodes.

Examples:
  Q: How many synonyms for C1234?
  A: MATCH (n:NCIT {code:'C1234'})-[:HAS_SYNONYM]->(s:SYN) RETURN n.term AS concept, count(s) AS synonym_count

  Q: Show synonyms for 'Lung Carcinoma'
  A: MATCH (n:NCIT) WHERE toLower(n.term) CONTAINS toLower('lung carcinoma') WITH n LIMIT 1 MATCH (n)-[:HAS_SYNONYM]->(s:SYN) RETURN n.code AS code, n.term AS concept, s.term AS synonym LIMIT 25

  Q: What CDEs use concept C4878?
  A: MATCH (ncit:NCIT {code:'C4878'})<-[:HAS_CONCEPT]-(pv:PV)<-[:HAS_PV]-(vdm:VDM)<-[:HAS_VDM]-(cde:CDE) RETURN cde.code AS cde_code, cde.term AS cde_term, pv.term AS pv_term LIMIT 25
"""

    def _get_ollama(self, cypher_model="gpt-4o"):
        if self._ollama_llm is not None and getattr(self, "current_cypher_model", None) == cypher_model:
            return self._ollama_llm
        try:
            from langchain_openai import ChatOpenAI
            if cypher_model.startswith("claude"):
                from langchain_anthropic import ChatAnthropic
                api_key = str(st.session_state.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", ""))
                llm = ChatAnthropic(model=cypher_model, temperature=0, api_key=api_key)
            else:
                api_key = str(st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY", ""))
                llm = ChatOpenAI(model=cypher_model, temperature=0, api_key=api_key)
            BackendClient._ollama_llm = llm
            BackendClient._ollama_available = True
            self.current_cypher_model = cypher_model
            return llm
        except Exception as e:
            BackendClient._ollama_available = False
            print(f"[BackendClient] LLM unavailable: {e}")
            return None

    @property
    def openai_ready(self) -> bool:
        return self._ollama_available is True or (
            self._ollama_available is None and self._get_ollama() is not None
        )

    def nl_to_cypher(self, question: str, system_prompt: str = None, cypher_model: str = "llama3.1") -> dict:
        prompt = system_prompt or self.GRAPH_SCHEMA_PROMPT
        cypher = None
        method = "pattern"

        llm = self._get_ollama(cypher_model=cypher_model)
        if llm is not None:
            try:
                raw = llm.invoke(f"{prompt}\n\nQuestion: {question}\nCypher:").strip()
                cleaned = raw
                match = _re.search(r'```(?:cypher)?\n?(.*?)```', cleaned, _re.DOTALL | _re.IGNORECASE)
                if match:
                    cleaned = match.group(1).strip()
                match2 = _re.search(r'(?i)\b(MATCH|CALL|WITH|UNWIND)\b.*?\bRETURN\b.*', cleaned, _re.DOTALL)
                if match2:
                    cleaned = match2.group(0).strip()
                if "RETURN" in cleaned.upper():
                    cypher = cleaned
                    method = "openai"
            except Exception as e:
                print(f"[nl_to_cypher] Ollama call failed: {e}")

        if cypher is None:
            cypher = self._pattern_cypher(question)
            method = "pattern"

        results = []
        error = None
        if self._driver:
            try:
                with self._driver.session() as session:
                    records = session.run(cypher)
                    results = [r.data() for r in records]
            except Exception as e:
                error = f"Cypher execution failed: {e}"

        return {
            "question": question, "cypher": cypher, "method": method,
            "results": results, "total": len(results), "error": error,
        }

    @staticmethod
    def _pattern_cypher(question: str) -> str:
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

        quoted = _re.findall(r"""[\"']([^\"']+)[\"']""", question)
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

    # ── EVS File Ingestion ────────────────────────────────────────────────

    @staticmethod
    def _parse_evs_tsv(content: str) -> list[dict]:
        rows = []
        for idx, line in enumerate(content.splitlines()):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            cols = line.split("\t")
            match_code = match_term = query_term = ""
            rank = None

            for c_i, c in enumerate(cols):
                if c.startswith("C") and c[1:].isdigit():
                    match_code = c
                    if c_i + 1 < len(cols):
                        match_term = cols[c_i + 1]
                    break

            if match_code:
                try:
                    mc_i = cols.index(match_code)
                    if mc_i > 0:
                        candidates = [x for x in cols[:mc_i] if x and len(x) >= 8 and " " in x]
                        if candidates:
                            query_term = candidates[-1]
                except ValueError:
                    pass

            if match_code and match_term:
                try:
                    mt_i = cols.index(match_term)
                    for t in cols[mt_i + 1:]:
                        if t.isdigit():
                            rank = int(t)
                            break
                except ValueError:
                    pass

            rows.append({
                "row_index": idx, "raw_line": line, "cols": cols,
                "query_term": query_term, "match_code": match_code,
                "match_term": match_term, "rank": rank,
            })
        return rows

    def ingest_evs_results_file(self, filename: str, content: str, source: str = "streamlit_upload") -> dict:
        if not self._driver:
            return {"ok": False, "file_id": None, "row_count": 0, "error": "Neo4j not connected"}

        parsed_rows = self._parse_evs_tsv(content)
        row_count = len(parsed_rows)
        file_hash = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()[:16]
        file_id = f"evs:{file_hash}"

        q_file = """
        MERGE (f:UploadFile {file_id: $file_id})
        SET f.filename = $filename, f.source = $source,
            f.uploaded_at = $uploaded_at, f.row_count = $row_count
        """
        r1 = self.write_cypher(q_file, {
            "file_id": file_id, "filename": filename, "source": source,
            "uploaded_at": datetime.utcnow().isoformat(), "row_count": row_count,
        })
        if not r1["ok"]:
            return {"ok": False, "file_id": None, "row_count": 0, "error": f"file MERGE failed: {r1['error']}"}

        q_rows = """
        UNWIND $rows AS row
        MERGE (r:UploadRow {row_id: row.row_id})
        SET r.file_id = $file_id, r.row_index = row.row_index,
            r.raw_line = row.raw_line, r.cols = row.cols,
            r.query_term = row.query_term, r.match_code = row.match_code,
            r.match_term = row.match_term, r.rank = row.rank
        WITH r
        MATCH (f:UploadFile {file_id: $file_id})
        MERGE (f)-[:HAS_ROW]->(r)
        """
        BATCH = 500
        for start in range(0, row_count, BATCH):
            chunk = parsed_rows[start:start + BATCH]
            rows_param = []
            for row in chunk:
                row_hash = hashlib.sha256(
                    (file_id + "|" + str(row["row_index"]) + "|" + row["raw_line"]).encode("utf-8", errors="ignore")
                ).hexdigest()[:20]
                rows_param.append({**row, "row_id": f"{file_id}:row:{row_hash}"})
            r2 = self.write_cypher(q_rows, {"file_id": file_id, "rows": rows_param})
            if not r2["ok"]:
                return {"ok": False, "file_id": file_id, "row_count": row_count, "error": f"row batch failed: {r2['error']}"}

        return {"ok": True, "file_id": file_id, "row_count": row_count, "error": None}

    # ── Status / Cleanup ──────────────────────────────────────────────────

    def status_dict(self) -> dict:
        return {
            "neo4j_connected": self.connected,
            "exact_match_ready": self._matcher is not None,
            "synonym_ready": self._synonyms is not None,
            "semantic_ready": self._searcher is not None,
            "agent_ready": self.agent_ready,
            "openai_ready": self._ollama_available is True,
            "claude_ready": self.claude_ready,
            "error": self.error,
        }

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


# ── Singleton accessor ────────────────────────────────────────────────────
_client_instance: Optional[BackendClient] = None


def get_client() -> BackendClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = BackendClient()
    return _client_instance
