"""
Accuracy Benchmark — compare Frederick's mapping against EVS ground truth.

Upload the CDA/EVS summary file (TSV with columns: unharmonized value,
cda_manual_harmonization_name, cda_manual_harmonization_code, evs_first_result_name,
evs_first_result_code, search_result). Frederick runs its own search cascade on each
term and we compare who finds the correct code more often.
"""

import io
import streamlit as st
import pandas as pd

from app.services.neo4j_client import BackendClient
from app.services.models import MatchResult


def _safe_str(val) -> str:
    return val if val is not None else ""


def _parse_ground_truth(uploaded) -> pd.DataFrame:
    """Parse the EVS summary TSV into a DataFrame."""
    content = uploaded.read().decode("utf-8", errors="replace")
    df = pd.read_csv(io.StringIO(content), sep="\t")

    # Normalize column names (strip whitespace, lowercase)
    df.columns = [c.strip() for c in df.columns]

    # Identify the key columns (handle slight naming variations)
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "unharmonized" in cl and "value" in cl:
            col_map["input_term"] = c
        elif "manual" in cl and "code" in cl:
            col_map["ground_truth_code"] = c
        elif "manual" in cl and "name" in cl:
            col_map["ground_truth_name"] = c
        elif "evs_first" in cl and "code" in cl:
            col_map["evs_code"] = c
        elif "evs_first" in cl and "name" in cl:
            col_map["evs_name"] = c
        elif "search_result" in cl:
            col_map["evs_category"] = c

    if "input_term" not in col_map or "ground_truth_code" not in col_map:
        st.error(
            "Could not find required columns. Expected: 'unharmonized value' and "
            "'cda_manual_harmonization_code' (or similar)."
        )
        return pd.DataFrame()

    # Rename to standard names
    rename = {v: k for k, v in col_map.items()}
    df = df.rename(columns=rename)

    # Drop the index column if present
    if df.columns[0].strip().isdigit() or df.columns[0] == "":
        df = df.iloc[:, 1:]

    return df


def _run_frederick_search(client: BackendClient, term: str, top_k: int = 10) -> list[dict]:
    """Run Frederick's search cascade on a single term."""
    matches = []

    # Exact
    exact = client.exact_match_by_term(term)
    if exact:
        matches.append({"code": _safe_str(exact.code), "term": _safe_str(exact.term),
                        "score": exact.score, "method": "exact"})

    # Fuzzy
    for f in client.fuzzy_match(term, limit=top_k):
        if not any(m["code"] == f.code for m in matches):
            matches.append({"code": _safe_str(f.code), "term": _safe_str(f.term),
                            "score": f.score, "method": "fuzzy"})

    # Synonym path
    for s in client.synonyms_by_term(term)[:top_k]:
        if not any(m["term"] == s for m in matches):
            matches.append({"code": "", "term": s, "score": 0.7, "method": "synonym_path"})

    # Semantic NCIT
    if len(matches) < top_k:
        for r in client.semantic_search_ncit(term, top_k=top_k):
            if not any(m["code"] == r.code for m in matches):
                matches.append({"code": _safe_str(r.code), "term": _safe_str(r.term),
                                "score": r.score, "method": "semantic_ncit"})

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:top_k]


def page_benchmark(client: BackendClient):
    st.markdown("## 📊 Accuracy Benchmark")
    st.caption(
        "Upload the CDA/EVS ground truth summary file, run Frederick's search on every term, "
        "and compare accuracy against EVS."
    )

    is_live = client.connected
    if not is_live:
        st.warning("⚠️ Neo4j offline — benchmark will use mock results (not meaningful)")

    # ── Upload ────────────────────────────────────────────────────────
    st.markdown("### 1. Upload ground truth")
    uploaded = st.file_uploader(
        "Upload EVS summary file (.txt / .tsv)",
        type=["txt", "tsv"],
        help="Tab-separated file with columns: unharmonized value, cda_manual_harmonization_code, etc.",
    )

    if not uploaded:
        st.info("Upload `cda_evs_results_summary_*.txt` to begin.")
        st.markdown("""
        **Expected columns:**
        - `unharmonized value` — the raw clinical term
        - `cda_manual_harmonization_code` — the human-assigned correct NCIT code
        - `cda_manual_harmonization_name` — the correct concept name
        - `evs_first_result_code` — what EVS returned as #1
        - `search_result` — EVS performance category
        """)
        return

    df = _parse_ground_truth(uploaded)
    if df.empty:
        return

    st.success(f"Loaded **{len(df)}** terms with ground truth.")

    with st.expander("Preview ground truth", expanded=False):
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    # ── EVS baseline stats ────────────────────────────────────────────
    if "evs_category" in df.columns:
        st.markdown("### 2. EVS baseline performance")
        evs_counts = df["evs_category"].value_counts()
        evs_total = len(df)

        # Compute EVS accuracy metrics
        evs_first_hit = 0
        evs_any_hit = 0
        evs_miss = 0
        for cat, count in evs_counts.items():
            cat_lower = cat.lower() if isinstance(cat, str) else ""
            if "first result" in cat_lower and "does not find" not in cat_lower:
                evs_first_hit += count
                evs_any_hit += count
            elif "after first" in cat_lower:
                evs_any_hit += count
            elif "does not find" in cat_lower:
                evs_miss += count

        ec = st.columns(4)
        with ec[0]:
            st.metric("Total terms", evs_total)
        with ec[1]:
            st.metric("EVS #1 hit", f"{evs_first_hit} ({100*evs_first_hit/evs_total:.1f}%)")
        with ec[2]:
            st.metric("EVS top-10 hit", f"{evs_any_hit} ({100*evs_any_hit/evs_total:.1f}%)")
        with ec[3]:
            st.metric("EVS miss", f"{evs_miss} ({100*evs_miss/evs_total:.1f}%)")

        with st.expander("EVS category breakdown"):
            for cat, count in evs_counts.items():
                st.markdown(f"- **{cat}**: {count} ({100*count/evs_total:.1f}%)")

    # ── Run Frederick ─────────────────────────────────────────────────
    st.markdown("### 3. Run Frederick benchmark")

    top_k = st.slider("Top K results per term", 1, 20, 10, key="bench_top_k")

    # Limit option for testing
    max_terms = st.number_input(
        "Max terms to test (0 = all)",
        min_value=0, max_value=len(df), value=0, step=50,
        help="Set to a small number (e.g. 50) for a quick test run.",
    )

    run = st.button("🚀 Run Frederick on all terms", type="primary", use_container_width=True)

    if run:
        terms_df = df if max_terms == 0 else df.head(max_terms)
        total = len(terms_df)

        results = []
        progress = st.progress(0, text="Running benchmark...")

        for i, (_, row) in enumerate(terms_df.iterrows()):
            progress.progress((i + 1) / total, text=f"({i+1}/{total}): {str(row.get('input_term', ''))[:40]}")

            input_term = str(row.get("input_term", ""))
            gt_code = str(row.get("ground_truth_code", "")).strip()
            gt_name = str(row.get("ground_truth_name", ""))
            evs_code = str(row.get("evs_code", "")).strip() if "evs_code" in row else ""
            evs_category = str(row.get("evs_category", "")) if "evs_category" in row else ""

            if not input_term.strip():
                continue

            # Run Frederick
            if is_live:
                fred_matches = _run_frederick_search(client, input_term, top_k=top_k)
            else:
                fred_matches = [{"code": f"C{abs(hash(input_term)) % 99999}", "term": f"Mock for {input_term}",
                                 "score": 0.5, "method": "mock"}]

            # Check if Frederick found the ground truth code
            fred_codes = [m["code"] for m in fred_matches]
            fred_first_code = fred_codes[0] if fred_codes else ""
            fred_first_name = fred_matches[0]["term"] if fred_matches else ""
            fred_first_method = fred_matches[0]["method"] if fred_matches else ""

            fred_first_hit = (fred_first_code == gt_code) if gt_code else False
            fred_any_hit = gt_code in fred_codes if gt_code else False
            fred_rank = (fred_codes.index(gt_code) + 1) if fred_any_hit else None

            evs_first_hit = (evs_code == gt_code) if gt_code and evs_code else False

            results.append({
                "Input Term": input_term,
                "Ground Truth Code": gt_code,
                "Ground Truth Name": gt_name,
                "EVS #1 Code": evs_code,
                "EVS Hit #1": "✅" if evs_first_hit else "❌",
                "EVS Category": evs_category,
                "Frederick #1 Code": fred_first_code,
                "Frederick #1 Name": fred_first_name,
                "Frederick #1 Method": fred_first_method,
                "Frederick Hit #1": "✅" if fred_first_hit else "❌",
                "Frederick Hit Top-K": "✅" if fred_any_hit else "❌",
                "Frederick Rank": fred_rank if fred_rank else "—",
            })

        progress.empty()
        results_df = pd.DataFrame(results)
        st.session_state["bench_results"] = results_df

    # ── Display results ───────────────────────────────────────────────
    if "bench_results" not in st.session_state:
        return

    results_df = st.session_state["bench_results"]
    total = len(results_df)

    st.markdown("---")
    st.markdown("### 4. Results — Frederick vs EVS")

    # Compute metrics
    fred_first_hits = (results_df["Frederick Hit #1"] == "✅").sum()
    fred_topk_hits = (results_df["Frederick Hit Top-K"] == "✅").sum()
    evs_first_hits = (results_df["EVS Hit #1"] == "✅").sum()
    fred_misses = total - fred_topk_hits

    # Summary metrics
    mc = st.columns(6)
    with mc[0]:
        st.metric("Terms tested", total)
    with mc[1]:
        st.metric("Frederick #1 hit", f"{fred_first_hits} ({100*fred_first_hits/total:.1f}%)")
    with mc[2]:
        st.metric("Frederick top-K hit", f"{fred_topk_hits} ({100*fred_topk_hits/total:.1f}%)")
    with mc[3]:
        st.metric("Frederick miss", f"{fred_misses} ({100*fred_misses/total:.1f}%)")
    with mc[4]:
        st.metric("EVS #1 hit", f"{evs_first_hits} ({100*evs_first_hits/total:.1f}%)")
    with mc[5]:
        diff = fred_first_hits - evs_first_hits
        sign = "+" if diff >= 0 else ""
        st.metric("Frederick vs EVS (#1)", f"{sign}{diff}", delta=f"{sign}{diff}")

    # Comparison chart
    st.markdown("##### Hit rate comparison")
    chart_df = pd.DataFrame({
        "Metric": ["#1 Hit Rate", "Top-K Hit Rate", "Miss Rate"],
        "Frederick": [
            100 * fred_first_hits / total,
            100 * fred_topk_hits / total,
            100 * fred_misses / total,
        ],
        "EVS": [
            100 * evs_first_hits / total,
            0,  # EVS top-10 data not directly in per-row comparison
            100 * (total - evs_first_hits) / total,
        ],
    })
    st.bar_chart(chart_df.set_index("Metric"), horizontal=True)

    # Detailed results table
    st.markdown("##### Detailed results")

    filter_col = st.columns(3)
    with filter_col[0]:
        show_filter = st.selectbox("Filter", [
            "All",
            "Frederick wins (Frederick ✅, EVS ❌)",
            "EVS wins (EVS ✅, Frederick ❌)",
            "Both hit",
            "Both miss",
        ])

    if show_filter == "Frederick wins (Frederick ✅, EVS ❌)":
        filtered = results_df[(results_df["Frederick Hit #1"] == "✅") & (results_df["EVS Hit #1"] == "❌")]
    elif show_filter == "EVS wins (EVS ✅, Frederick ❌)":
        filtered = results_df[(results_df["EVS Hit #1"] == "✅") & (results_df["Frederick Hit #1"] == "❌")]
    elif show_filter == "Both hit":
        filtered = results_df[(results_df["Frederick Hit #1"] == "✅") & (results_df["EVS Hit #1"] == "✅")]
    elif show_filter == "Both miss":
        filtered = results_df[(results_df["Frederick Hit #1"] == "❌") & (results_df["EVS Hit #1"] == "❌")]
    else:
        filtered = results_df

    st.caption(f"Showing {len(filtered)} of {total} rows")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    # Export
    exp = st.columns([1, 1, 4])
    with exp[0]:
        st.download_button(
            "📥 Export full results CSV",
            results_df.to_csv(index=False),
            "frederick_vs_evs_benchmark.csv",
            "text/csv",
        )
    with exp[1]:
        if st.button("✕ Clear benchmark"):
            del st.session_state["bench_results"]
            st.rerun()