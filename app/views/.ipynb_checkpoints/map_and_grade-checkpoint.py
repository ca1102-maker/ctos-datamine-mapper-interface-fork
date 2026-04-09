"""
Map & Grade — unified term mapping with batch upload, inline grading, and selective export.

Flow:
  1. User inputs terms (text area, CSV upload, or TXT upload)
  2. System runs search cascade: exact → fuzzy → semantic
  3. Results displayed per-term with checkbox (select for export) and ranking dropdown
  4. Export only selected rows as CSV/JSON
"""

import io
import csv
import streamlit as st
import pandas as pd

from app.services.neo4j_client import BackendClient
from app.services.models import MatchResult


def _safe_str(val) -> str:
    """Coerce None to empty string."""
    return val if val is not None else ""


def _truncate(text, max_len=80) -> str:
    s = _safe_str(text)
    return (s[:max_len] + "...") if len(s) > max_len else s


def _parse_upload(uploaded) -> list[str]:
    """Parse an uploaded file into a deduplicated list of terms."""
    content = uploaded.read().decode("utf-8", errors="replace")
    raw_terms = []

    if uploaded.name.endswith(".csv"):
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            if row and row[0].strip():
                t = row[0].strip()
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

    seen = set()
    terms = []
    for t in raw_terms:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            terms.append(t)
    return terms


def _run_search(client: BackendClient, term: str, search_mode: str, top_k: int) -> list[dict]:
    """Run the search cascade for a single term."""
    matches = []

    if search_mode.startswith("Auto"):
        exact = client.exact_match_by_term(term)
        if exact:
            matches.append(_result_to_dict(exact, "exact"))
        for f in client.fuzzy_match(term, limit=top_k):
            if not any(m["code"] == f.code for m in matches):
                matches.append(_result_to_dict(f, "fuzzy"))
        for s in client.synonyms_by_term(term)[:top_k]:
            if not any(m["term"] == s for m in matches):
                matches.append({
                    "code": "", "term": s, "definition": "",
                    "type": "SYN", "method": "synonym_path", "score": 0.7,
                })
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

    matches.sort(key=lambda x: x["score"], reverse=True)
    for i, m in enumerate(matches):
        m["rank"] = i + 1

    return matches[:top_k]


def _result_to_dict(r: MatchResult, method: str) -> dict:
    return {
        "code": _safe_str(r.code),
        "term": _safe_str(r.term),
        "definition": _safe_str(r.definition),
        "type": _safe_str(r.node_type),
        "method": method,
        "score": r.score,
    }


def _generate_mock(term: str, top_k: int) -> list[dict]:
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


def _grade_key(input_term: str, m: dict) -> str:
    return f"{input_term}|{_safe_str(m.get('code'))}|{_safe_str(m.get('term'))}"


def page_map_and_grade(client: BackendClient):
    st.markdown("## 🎯 Map & Grade")
    st.caption(
        "Upload terms (CSV, TXT, or type manually), map them to NCIT/caDSR, "
        "grade the results, and export selected matches."
    )

    is_live = client.connected
    if is_live:
        st.success("🔗 Connected to live Neo4j", icon="✅")
    else:
        st.warning("⚠️ Neo4j offline — showing mock results")

    # ── 1. Input ──────────────────────────────────────────────────────
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

    # ── 2. Configure ──────────────────────────────────────────────────
    st.markdown("### 2. Configure search")
    cfg_cols = st.columns([2, 1, 1])

    with cfg_cols[0]:
        search_mode = st.selectbox(
            "Search strategy",
            [
                "Auto (exact → fuzzy → synonym → semantic)",
                "Exact only", "Fuzzy only", "Semantic PV", "Semantic NCIT",
                "Semantic CDE definition", "Semantic NCIT definition",
            ],
        )
    with cfg_cols[1]:
        top_k = st.slider("Results per term", 3, 20, 5)
    with cfg_cols[2]:
        threshold = st.slider("Min score", 0.0, 1.0, 0.3, 0.05)

    # ── 3. Run ────────────────────────────────────────────────────────
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

            matches = [m for m in matches if m["score"] >= threshold]
            results_by_term[term] = matches

        progress.empty()
        st.session_state["mg_results"] = results_by_term
        st.session_state["mg_grades"] = {}
        st.session_state["mg_selected"] = {}

    # ── 4. Results ────────────────────────────────────────────────────
    if not st.session_state.get("mg_results"):
        return

    results = st.session_state["mg_results"]
    grades = st.session_state.setdefault("mg_grades", {})
    selected = st.session_state.setdefault("mg_selected", {})

    st.markdown("---")
    st.markdown("### 3. Results & grading")

    # Summary bar (counts will be accurate because checkboxes read from session_state set on previous run)
    total_matches = sum(len(v) for v in results.values())
    avg_score = (
        sum(m["score"] for ms in results.values() for m in ms) / total_matches
        if total_matches > 0 else 0
    )

    # Select all toggle + clear + export
    ctrl_cols = st.columns([1, 1, 1, 1, 2])
    with ctrl_cols[0]:
        select_all = st.checkbox(
            "Select all",
            value=st.session_state.get("mg_select_all", False),
            key="mg_select_all_widget",
        )
        prev_select_all = st.session_state.get("mg_select_all", False)
        if select_all != prev_select_all:
            st.session_state["mg_select_all"] = select_all
            for input_term, matches in results.items():
                for m in matches:
                    gk = _grade_key(input_term, m)
                    selected[gk] = select_all
                    # Write directly to widget key so checkboxes visually update
                    st.session_state[f"sel_{gk}"] = select_all
            st.rerun()

    # Build export data before rendering buttons (reads from selected dict which
    # was populated on the previous rerun by the checkbox widgets below)
    all_rows = []
    selected_rows = []
    for input_term, matches in results.items():
        for m in matches:
            gk = _grade_key(input_term, m)
            # Sync from widget key (source of truth after user interaction)
            widget_key = f"sel_{gk}"
            if widget_key in st.session_state:
                selected[gk] = st.session_state[widget_key]
            row = {
                "Input Term": input_term,
                "Rank": m.get("rank", ""),
                "Code": _safe_str(m["code"]),
                "Matched Term": _safe_str(m["term"]),
                "Definition": _safe_str(m.get("definition")),
                "Type": _safe_str(m.get("type")),
                "Method": m["method"],
                "Score": m["score"],
                "Grade": grades.get(gk, ""),
            }
            all_rows.append(row)
            if selected.get(gk):
                selected_rows.append(row)

    selected_count = len(selected_rows)
    export_data = selected_rows if selected_rows else all_rows
    export_label = f"📥 Export selected ({selected_count})" if selected_rows else "📥 Export all"

    with ctrl_cols[1]:
        st.download_button(
            export_label,
            pd.DataFrame(export_data).to_csv(index=False),
            "frederick_mapping_results.csv",
            "text/csv",
        )
    with ctrl_cols[2]:
        st.download_button(
            "📥 JSON",
            pd.DataFrame(export_data).to_json(orient="records", indent=2),
            "frederick_mapping_results.json",
            "application/json",
        )
    with ctrl_cols[3]:
        if st.button("✕ Clear results"):
            st.session_state["mg_results"] = {}
            st.session_state["mg_grades"] = {}
            st.session_state["mg_selected"] = {}
            st.session_state["mg_select_all"] = False
            st.rerun()

    # Summary bar
    sum_cols = st.columns(4)
    with sum_cols[0]:
        st.metric("Terms mapped", len(results))
    with sum_cols[1]:
        st.metric("Total matches", total_matches)
    with sum_cols[2]:
        st.metric("Avg score", f"{avg_score:.3f}")
    with sum_cols[3]:
        st.metric("Selected for export", f"{selected_count}/{total_matches}")

    # ── Per-term results with checkbox + ranking ──────────────────────
    grade_options = ["—", "✅ Accept", "🤔 Maybe", "❌ Reject"]

    for input_term, matches in results.items():
        with st.expander(
            f"**{input_term}** — {len(matches)} match{'es' if len(matches) != 1 else ''}",
            expanded=len(results) <= 10,
        ):
            if not matches:
                st.caption("No matches found above threshold.")
                continue

            # Each match gets a row: checkbox | rank | code | term | score | method | grade dropdown
            for j, m in enumerate(matches):
                gk = _grade_key(input_term, m)
                col_check, col_rank, col_code, col_term, col_score, col_method, col_grade = st.columns(
                    [0.5, 0.5, 1, 2.5, 0.7, 1, 1.5]
                )

                with col_check:
                    # Default only if widget key doesn't exist yet
                    if f"sel_{gk}" not in st.session_state:
                        st.session_state[f"sel_{gk}"] = selected.get(gk, False)
                    is_selected = st.checkbox(
                        "sel",
                        key=f"sel_{gk}",
                        label_visibility="collapsed",
                    )
                    selected[gk] = is_selected

                with col_rank:
                    st.markdown(f"**#{m.get('rank', j+1)}**")

                with col_code:
                    st.code(_safe_str(m["code"]) or "—", language=None)

                with col_term:
                    st.markdown(f"**{_safe_str(m['term'])}**")
                    defn = _truncate(m.get("definition"), 60)
                    if defn:
                        st.caption(defn)

                with col_score:
                    score = m["score"]
                    color = "#059669" if score >= 0.9 else ("#d97706" if score >= 0.7 else "#94a3b8")
                    st.markdown(f'<span style="color:{color};font-weight:600;">{score:.3f}</span>', unsafe_allow_html=True)

                with col_method:
                    st.caption(m["method"])

                with col_grade:
                    current = grades.get(gk, "—")
                    grade = st.selectbox(
                        "grade",
                        grade_options,
                        index=grade_options.index(current) if current in grade_options else 0,
                        key=f"grade_{gk}",
                        label_visibility="collapsed",
                    )
                    grades[gk] = grade

            st.markdown("---")

    # ── Grading summary ───────────────────────────────────────────────
    active_grades = {k: v for k, v in grades.items() if v != "—"}
    if active_grades:
        st.markdown("### Grading summary")
        grade_counts = {"✅ Accept": 0, "🤔 Maybe": 0, "❌ Reject": 0}
        for g in active_grades.values():
            if g in grade_counts:
                grade_counts[g] += 1
        gc = st.columns(3)
        with gc[0]:
            st.metric("Accepted", grade_counts["✅ Accept"])
        with gc[1]:
            st.metric("Maybe", grade_counts["🤔 Maybe"])
        with gc[2]:
            st.metric("Rejected", grade_counts["❌ Reject"])

    # ── Quick synonym lookup (sidebar) ────────────────────────────────
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