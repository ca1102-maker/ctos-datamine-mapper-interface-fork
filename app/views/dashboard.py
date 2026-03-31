"""Dashboard — KPI overview (mock data for now)."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.services.neo4j_client import BackendClient


def _metric_card(label, value, change, trend="up"):
    cls = "change-up" if trend == "up" else "change-down"
    arrow = "↑" if trend == "up" else "↓"
    st.markdown(
        f"""<div class="metric-card">
        <h4>{label}</h4>
        <div style="display:flex;align-items:flex-end;justify-content:space-between;">
            <span class="value">{value}</span><span class="{cls}">{arrow} {change}</span>
        </div></div>""",
        unsafe_allow_html=True,
    )


def page_dashboard(client: BackendClient):
    st.markdown("## 📊 Dashboard")
    st.caption("Overview of system performance and activity.")

    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card("Total Queries", "45,392", "+15.3%", "up")
    with c2: _metric_card("Graph Nodes", "8,247", "+523", "up")
    with c3: _metric_card("Accuracy", "94.2%", "+2.1%", "up")
    with c4: _metric_card("Response Time", "0.34s", "-0.08s", "down")

    col_chart, col_pie = st.columns([2, 1])
    with col_chart:
        st.markdown("##### Query Volume")
        dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        queries = [1200 + (i * 37 % 800) + i * 10 for i in range(30)]
        successful = [1100 + (i * 29 % 800) + i * 9 for i in range(30)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=queries, name="Total Queries", line=dict(color="#374151", width=2)))
        fig.add_trace(go.Scatter(x=dates, y=successful, name="Successful", line=dict(color="#10b981", width=2)))
        fig.update_layout(
            height=320, margin=dict(l=40, r=20, t=20, b=40),
            legend=dict(orientation="h", y=-0.15),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    with col_pie:
        st.markdown("##### Query Categories")
        fig_pie = go.Figure(data=[go.Pie(
            labels=["Search", "Analysis", "Visualization", "Export", "Other"],
            values=[35, 28, 20, 12, 5], hole=0.5,
            marker=dict(colors=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#6b7280"]),
        )])
        fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("##### Recent Activity")
    activities = [
        ("10:00 AM", "Alice Chen", "Uploaded dataset", "success"),
        ("10:30 AM", "Bob Smith", "Ran analysis", "success"),
        ("11:00 AM", "Carol Davis", "Created visualization", "warning"),
        ("11:30 AM", "David Lee", "Exported report", "success"),
        ("12:00 PM", "Emma Wilson", "Updated model", "success"),
    ]
    for t, user, action, status in activities:
        badge = f'<span class="badge-{status}">{status.capitalize()}</span>'
        st.markdown(
            f'<div class="activity-row"><div style="display:flex;align-items:center;gap:1rem;">'
            f'<span style="font-size:0.75rem;color:#94a3b8;width:4rem;">{t}</span>'
            f'<span style="font-size:0.85rem;font-weight:500;color:#0f172a;width:7rem;">{user}</span>'
            f'<span style="font-size:0.85rem;color:#64748b;">{action}</span></div>{badge}</div>',
            unsafe_allow_html=True,
        )
