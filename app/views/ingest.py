"""Ingest Data — upload EVS results files into Neo4j."""

import streamlit as st
import pandas as pd

from app.services.neo4j_client import BackendClient


def page_ingest(client: BackendClient):
    st.markdown("## 📤 Ingest EVS Data")
    st.caption("Upload an EVS results file (TSV) and ingest rows into Neo4j as UploadFile/UploadRow nodes.")

    if not client.connected:
        st.error("Neo4j is not connected. Fix connection in Settings before ingesting.")
        return

    # Re-verify last ingested file
    st.markdown("### Re-verify last ingested file")
    last_file_id = st.session_state.get("last_ingested_file_id")
    if last_file_id:
        st.caption(f"Last file_id: `{last_file_id}`")
        if st.button("🔁 Run verification again", key="reverify"):
            q = """
            MATCH (f:UploadFile {file_id: $file_id})-[:HAS_ROW]->(r:UploadRow)
            RETURN f.filename AS filename, f.row_count AS row_count, count(r) AS rows_linked
            """
            rows = client.run_cypher(q, {"file_id": last_file_id})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            sample_q = """
            MATCH (f:UploadFile {file_id: $file_id})-[:HAS_ROW]->(r:UploadRow)
            RETURN r.row_index AS row_index, r.query_term AS query_term,
                   r.match_code AS match_code, r.match_term AS match_term, r.rank AS rank
            ORDER BY r.row_index ASC LIMIT 10
            """
            st.dataframe(pd.DataFrame(client.run_cypher(sample_q, {"file_id": last_file_id})),
                         use_container_width=True, hide_index=True)
    else:
        st.info("No previous ingest found yet in this session.")

    st.markdown("---")

    # Upload
    uploaded = st.file_uploader(
        "Upload EVS results file (.txt/.tsv)",
        type=["txt", "tsv"],
        help="Tab-delimited EVS output. We'll ingest each row into Neo4j.",
    )

    if not uploaded:
        st.info("Choose a file to begin.")
        return

    content = uploaded.read().decode("utf-8", errors="replace")
    lines = [ln for ln in content.splitlines() if ln.strip()]
    st.write(f"Detected **{len(lines)}** non-empty lines.")
    st.code("\n".join(lines[:10]), language="text")

    st.markdown("---")
    confirm = st.checkbox("I understand this will WRITE to the Neo4j database.", value=False)

    if st.button("🚀 Ingest into Neo4j", type="primary", disabled=not confirm):
        with st.spinner("Ingesting..."):
            result = client.ingest_evs_results_file(
                filename=uploaded.name, content=content,
                source="streamlit:ingest_page",
            )
        if not result["ok"]:
            st.error(f"Upload failed: {result['error']}")
            return

        st.success(f"✅ Ingested {result['row_count']} rows (file_id={result['file_id']})")
        st.session_state["last_ingested_file_id"] = result["file_id"]

        q = """
        MATCH (f:UploadFile {file_id: $file_id})-[:HAS_ROW]->(r:UploadRow)
        RETURN f.filename AS filename, f.row_count AS row_count, count(r) AS rows_linked
        """
        st.dataframe(
            pd.DataFrame(client.run_cypher(q, {"file_id": result["file_id"]})),
            use_container_width=True, hide_index=True,
        )
