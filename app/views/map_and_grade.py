"""
Map & Grade — unified term mapping with batch upload and inline SME grading.

Merges the old Semantic Mapping and SME Workbench pages. Flow:
  1. User inputs terms (text area, CSV upload, or TXT upload)
  2. System runs search cascade: exact → fuzzy → semantic
  3. Results displayed in grouped table with per-term grading
  4. Export CSV/JSON with grades included
"""

import io
import csv
import streamlit as st
import pandas as pd

from app.services.neo4j_client import BackendClient
from app.services.models import MatchResult


def _parse_upload(uploaded) -> list[str]:
    """Parse an uploaded file into a deduplicated list of terms."""
    content = uploaded.read().decode("utf-8", errors="replace")
    raw_terms = []

    if uploaded.name.endswith(".csv"):
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            if row and row[0].strip():
                t = row[0].strip()
                # Skip obvious headers
                if t.lower() not in ("term", "terms", "input", "query", "name", "category"):
                    raw_terms.append(t)
    elif "\t" in content:
        for line in content.strip().splitlines():
            parts = line.split("\t")
            t = parts[0].strip()
            if t and not t.lower().startswith("term") and not t.startswith("#"):
                raw_terms.append(t)
    else:
        for line in content.strip().splitlines():
            t = line.strip()
            if t and not t.startswith("#"):
                raw_terms.append(t)

    # Deduplicate preserving order
    seen = set()
    terms = []
    for t in raw_terms:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            terms.append(t)
    return terms


def _deterministic_hash(s: str) -> float:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return (h % 100000) / 100000


def _run_search(client: BackendClient, term: str, search_mode: str, top_k: int) -> list[dict]:
    """Run the search cascade for a single term. Returns list of result dicts."""
    matches = []

    if search_mode.startswith("Auto"):
        # 1) Exact
        exact = client.exact_match_by_term(term)
        if exact:
            matches.append(_result_to_dict(exact, "exact"))
        # 2) Fuzzy
        for f in client.fuzzy_match(term, limit=top_k):
            if not any(m["code"] == f.code for m in matches):
                matches.append(_result_to_dict(f, "fuzzy"))
        # 3) Synonym path
        for s in client.synonyms_by_term(term)[:top_k]:
            if not any(m["term"] == s for m in matches):
                matches.append({
                    "code": "", "term": s, "definition": "",
                    "type": "SYN", "method": "synonym_path", "score": 0.7,
                })
        # 4) Semantic NCIT (fill remaining slots)
        if len(matches) < top_k:
            for r in client.semantic_search_ncit(term, top_k=top_k):
                if not any(m["code"] == r.code for m in matches):
                    matches.append(_result_to_dict(r, r.source))
    elif search_mode == "Exact only":
        r = client.exact_match_by_term(term)
        if r:
            matches.append(_result_to_dict(r, "exact"))
        else:
            r = client.exact_match_by_code(term)
            if r:
                matches.append(_result_to_dict(r, "exact"))
    elif search_mode == "Fuzzy only":
        for f in client.fuzzy_match(term, limit=top_k):
            matches.append(_result_to_dict(f, "fuzzy"))
    elif search_mode == "Semantic PV":
        for r in client.semantic_search_pv(term, top_k=top_k):
            matches.append(_result_to_dict(r, r.source))
    elif search_mode == "Semantic NCIT":
        for r in client.semantic_search_ncit(term, top_k=top_k):
            matches.append(_result_to_dict(r, r.source))
    elif search_mode == "Semantic CDE definition":
        for r in client.semantic_search_cde_definition(term, top_k=top_k):
            matches.append(_result_to_dict(r, r.source))
    elif search_mode == "Semantic NCIT definition":
        for r in client.semantic_search_ncit_definition(term, top_k=top_k):
            matches.append(_result_to_dict(r, r.source))

    # Re-rank by score, assign ranks
    matches.sort(key=lambda x: x["score"], reverse=True)
    for i, m in enumerate(matches):
        m["rank"] = i + 1

    return matches[:top_k]


def _result_to_dict(r: MatchResult, method: str) -> dict:
    return {
        "code": r.code, "term": r.term, "definition": r.definition,
        "type": r.node_type, "method": method, "score": r.score,
    }


def _generate_mock(term: str, top_k: int) -> list[dict]:
    """Mock results when Neo4j is offline."""
    results = []
    for j in range(min(top_k, 5)):
        results.append({
            "rank": j + 1,
            "code": f"C{int(10000 + abs(hash(term + str(j))) % 90000)}",
            "term": f"Mock match {j+1} for {term}",
            "definition": f"Simulated definition for '{term}'.",
            "type": "NCIT", "method": "mock",
            "score": round(0.95 - j * 0.08, 3),
        })
    return results


def page_map_and_grade(client: BackendClient):
    st.markdown("## 🎯 Map & Grade")
    st.caption(
        "Upload terms (CSV, TXT, or type manually), map them to NCIT/caDSR, "
        "grade the results, and export."
    )

    is_live = client.connected
    if is_live:
        st.success("🔗 Connected to live Neo4j", icon="✅")
    else:
        st.warning("⚠️ Neo4j offline — showing mock results")

    # ── Input section ─────────────────────────────────────────────────
    st.markdown("### 1. Input terms")

    input_mode = st.radio(
        "Input method",
        ["📄 Upload file (CSV / TXT)", "⌨️ Type or paste"],
        horizontal=True,
    )

    terms: list[str] = []

    if input_mode.startswith("📄"):
        uploaded = st.file_uploader(
            "Upload your terms file",
            type=["csv", "txt", "tsv"],
            help="One term per line, or CSV with terms in the first column.",
        )
        if uploaded:
            terms = _parse_upload(uploaded)
            st.info(f"Parsed **{len(terms)}** unique terms from `{uploaded.name}`")
            if terms:
                with st.expander("Preview parsed terms", expanded=False):
                    st.write(terms[:50])
                    if len(terms) > 50:
                        st.caption(f"... and {len(terms) - 50} more")
    else:
        manual = st.text_area(
            "Enter terms (one per line)",
            placeholder="Lung Carcinoma\nProstate\nDiabetes Mellitus\nAtrial Fibrillation",
            height=140,
        )
        if manual.strip():
            if "," in manual and "\n" not in manual.strip():
                terms = [t.strip() for t in manual.split(",") if t.strip()]
            else:
                terms = [t.strip() for t in manual.strip().splitlines() if t.strip()]

    # ── Search configuration ──────────────────────────────────────────
    st.markdown("### 2. Configure search")
    cfg_cols = st.columns([2, 1, 1])

    with cfg_cols[0]:
        search_mode = st.selectbox(
            "Search strategy",
            [
                "Auto (exact → fuzzy → synonym → semantic)",
                "Exact only",
                "Fuzzy only",
                "Semantic PV",
                "Semantic NCIT",
                "Semantic CDE definition",
                "Semantic NCIT definition",
            ],
        )
    with cfg_cols[1]:
        top_k = st.slider("Results per term", 3, 20, 5)
    with cfg_cols[2]:
        threshold = st.slider("Min score", 0.0, 1.0, 0.3, 0.05)

    # ── Run ───────────────────────────────────────────────────────────
    run = st.button(
        f"🎯 Map {len(terms)} term{'s' if len(terms) != 1 else ''}",
        type="primary",
        disabled=not terms,
        use_container_width=True,
    )

    if run and terms:
        results_by_term: dict[str, list[dict]] = {}
        progress = st.progress(0, text="Mapping terms...")

        for i, term in enumerate(terms):
            progress.progress(
                (i + 1) / len(terms),
                text=f"Mapping ({i+1}/{len(terms)}): {term}",
            )
            if is_live:
                matches = _run_search(client, term, search_mode, top_k)
            else:
                matches = _generate_mock(term, top_k)

            # Apply threshold
            matches = [m for m in matches if m["score"] >= threshold]
            results_by_term[term] = matches

        progress.empty()
        st.session_state["mg_results"] = results_by_term
        # Reset grades for new run
        st.session_state["mg_grades"] = {}

    # ── Results section ───────────────────────────────────────────────
    if not st.session_state.get("mg_results"):
        return

    results = st.session_state["mg_results"]
    grades = st.session_state.setdefault("mg_grades", {})

    total_matches = sum(len(v) for v in results.values())
    avg_score = (
        sum(m["score"] for ms in results.values() for m in ms) / total_matches
        if total_matches > 0
        else 0
    )

    st.markdown("---")
    st.markdown("### 3. Results & grading")

    # Summary bar
    sum_cols = st.columns(4)
    with sum_cols[0]:
        st.metric("Terms mapped", len(results))
    with sum_cols[1]:
        st.metric("Total matches", total_matches)
    with sum_cols[2]:
        st.metric("Avg score", f"{avg_score:.3f}")
    with sum_cols[3]:
        graded_count = sum(1 for g in grades.values() if g != "—")
        st.metric("Graded", f"{graded_count}/{total_matches}")

    # Export buttons
    export_rows = []
    for input_term, matches in results.items():
        for m in matches:
            grade_key = f"{input_term}|{m['code']}|{m['term']}"
            export_rows.append({
                "Input Term": input_term,
                "Rank": m.get("rank", ""),
                "Code": m["code"],
                "Matched Term": m["term"],
                "Definition": m["definition"],
                "Type": m.get("type", ""),
                "Method": m["method"],
                "Score": m["score"],
                "Grade": grades.get(grade_key, ""),
            })
    export_df = pd.DataFrame(export_rows)

    exp_cols = st.columns([1, 1, 1, 3])
    with exp_cols[0]:
        st.download_button(
            "📥 Export CSV",
            export_df.to_csv(index=False),
            "frederick_mapping_results.csv",
            "text/csv",
        )
    with exp_cols[1]:
        st.download_button(
            "📥 Export JSON",
            export_df.to_json(orient="records", indent=2),
            "frederick_mapping_results.json",
            "application/json",
        )
    with exp_cols[2]:
        if st.button("✕ Clear results"):
            st.session_state["mg_results"] = {}
            st.session_state["mg_grades"] = {}
            st.rerun()

    # Per-term results with inline grading
    for input_term, matches in results.items():
        with st.expander(
            f"**{input_term}** — {len(matches)} match{'es' if len(matches) != 1 else ''}",
            expanded=len(results) <= 10,
        ):
            if not matches:
                st.caption("No matches found above threshold.")
                continue

            # Results table
            df = pd.DataFrame([
                {
                    "Rank": m.get("rank", ""),
                    "Code": m["code"],
                    "Term": m["term"],
                    "Score": m["score"],
                    "Method": m["method"],
                    "Definition": (m["definition"][:80] + "...") if len(m["definition"]) > 80 else m["definition"],
                }
                for m in matches
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Inline grading — one row of buttons per match
            st.caption("Grade matches:")
            grade_options = ["—", "✅ Accept", "🤔 Maybe", "❌ Reject"]

            grade_cols = st.columns(min(len(matches), 5))
            for j, m in enumerate(matches[:5]):
                with grade_cols[j]:
                    grade_key = f"{input_term}|{m['code']}|{m['term']}"
                    current = grades.get(grade_key, "—")
                    grade = st.selectbox(
                        f"#{m.get('rank', j+1)} {m['term'][:18]}",
                        grade_options,
                        index=grade_options.index(current) if current in grade_options else 0,
                        key=f"grade_{grade_key}",
                    )
                    if grade != current:
                        grades[grade_key] = grade

    # ── Grading summary ───────────────────────────────────────────────
    if any(g != "—" for g in grades.values()):
        st.markdown("---")
        st.markdown("### Grading summary")
        grade_counts = {"✅ Accept": 0, "🤔 Maybe": 0, "❌ Reject": 0}
        for g in grades.values():
            if g in grade_counts:
                grade_counts[g] += 1
        gc = st.columns(3)
        with gc[0]:
            st.metric("Accepted", grade_counts["✅ Accept"])
        with gc[1]:
            st.metric("Maybe", grade_counts["🤔 Maybe"])
        with gc[2]:
            st.metric("Rejected", grade_counts["❌ Reject"])

    # ── Quick synonym lookup (sidebar utility) ────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("##### Quick Synonym Lookup")
        syn_input = st.text_input("Term or code", key="syn_input", placeholder="e.g. prostate or C7378")
        if syn_input.strip():
            if syn_input.strip().upper().startswith("C") and syn_input.strip()[1:].isdigit():
                syns = client.synonyms_by_code(syn_input.strip())
            else:
                syns = client.synonyms_by_term(syn_input.strip())
            if syns:
                for s in syns:
                    st.markdown(f"- {s}")
            else:
                st.caption("No synonyms found" + (" (Neo4j offline)" if not is_live else ""))
