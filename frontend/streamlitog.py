import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import math
import requests
import json

# Page configuration
st.set_page_config(
    page_title="Frederick Platform",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #4fc3f7, #29b6f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton > button {
        background: linear-gradient(90deg, #4fc3f7, #29b6f6);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(79, 195, 247, 0.3);
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-left: 3px solid #4fc3f7;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None

# Sidebar navigation
with st.sidebar:
    st.markdown("## 🔬 Frederick Platform")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "💬 AI Chat", "🔗 Graph Visualization", "📊 Metrics", "📁 File Upload"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Active Users", "2,847", "12%")
    with col2:
        st.metric("Documents", "15.2K", "8%")

    st.markdown("---")
    with st.expander("⚙️ Settings"):
        theme = st.selectbox("Theme", ["Dark", "Light", "Auto"])
        notifications = st.checkbox("Enable notifications", value=True)
        api_endpoint = st.text_input("API Endpoint", "https://api.frederick.ai")

    st.markdown("---")
    if st.button("📤 Export Data"):
        st.success("Data export initiated!")

    st.markdown("---")
    st.caption("Frederick v2.0.1 | © 2025")

# Main content area
if page == "🏠 Dashboard":
    st.markdown('<h1 class="main-header">Frederick Dashboard</h1>', unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Queries", "45,392", "↑ 15.3%", help="Total queries processed this month")
    with col2:
        st.metric("Graph Nodes", "8,247", "↑ 523", help="Total nodes in knowledge graph")
    with col3:
        st.metric("Accuracy", "94.2%", "↑ 2.1%", help="Model accuracy score")
    with col4:
        st.metric("Response Time", "0.34s", "↓ 0.08s", help="Average response time")

    st.markdown("---")

    # Charts section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 Query Volume Over Time")
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        query_data = pd.DataFrame({
            'Date': dates,
            'Queries': np.random.randint(1200, 2000, 30) + np.arange(30) * 10,
            'Successful': np.random.randint(1100, 1900, 30) + np.arange(30) * 9,
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=query_data['Date'], y=query_data['Queries'],
                                 mode='lines+markers', name='Total Queries',
                                 line=dict(color='#4fc3f7', width=3)))
        fig.add_trace(go.Scatter(x=query_data['Date'], y=query_data['Successful'],
                                 mode='lines+markers', name='Successful',
                                 line=dict(color='#4caf50', width=2)))
        fig.update_layout(
            template='plotly_dark',
            height=400,
            hovermode='x unified',
            showlegend=True,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Query Categories")
        categories = pd.DataFrame({
            'Category': ['Search', 'Analysis', 'Visualization', 'Export', 'Other'],
            'Count': [35, 28, 20, 12, 5]
        })

        fig = go.Figure(data=[go.Pie(
            labels=categories['Category'],
            values=categories['Count'],
            hole=0.4,
            marker_colors=['#4fc3f7', '#4caf50', '#ff9800', '#9c27b0', '#607d8b']
        )])
        fig.update_layout(
            template='plotly_dark',
            height=400,
            showlegend=True,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Recent Activity
    st.markdown("---")
    st.subheader("📋 Recent Activity")
    activity_data = pd.DataFrame({
        'Time': pd.date_range(start='2025-01-20 10:00', periods=10, freq='30min'),
        'User': ['Alice Chen', 'Bob Smith', 'Carol Davis', 'David Lee', 'Emma Wilson',
                 'Frank Johnson', 'Grace Brown', 'Henry Taylor', 'Iris Martinez', 'Jack Anderson'],
        'Action': ['Uploaded dataset', 'Ran analysis', 'Created visualization', 'Exported report',
                   'Updated model', 'Queried database', 'Modified graph', 'Shared dashboard',
                   'Trained model', 'Reviewed results'],
        'Status': ['✅ Success', '✅ Success', '⚠️ Warning', '✅ Success', '✅ Success',
                   '✅ Success', '✅ Success', '✅ Success', '⏳ Processing', '✅ Success']
    })
    st.dataframe(activity_data, use_container_width=True, hide_index=True)

elif page == "💬 AI Chat":
    st.markdown('<h1 class="main-header">RAG AI Assistant</h1>', unsafe_allow_html=True)

    # Chat configuration
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        model = st.selectbox("Model", ["GPT-4", "Claude-3", "Llama-2", "Custom RAG"])
    with col2:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
    with col3:
        context = st.text_input("Context Filter", placeholder="e.g., medical, financial, technical...")

    st.markdown("---")

    # Chat interface
    chat_container = st.container()

    with chat_container:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask anything about your knowledge base..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Simulate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                import time

                time.sleep(1)

                # Mock RAG response
                response = f"""Based on the knowledge base, here's what I found:

**Relevant Documents:** 3 matches found
- Document A (95% relevance): Contains information about {prompt[:20]}...
- Document B (87% relevance): Related context on the topic
- Document C (76% relevance): Supporting information

**Answer:** 
This is a simulated response to your query about "{prompt}". In a real implementation, 
this would retrieve relevant information from your vector database and provide a 
synthesized answer based on your documents.

**Confidence Score:** 92%
**Sources:** [Doc-2847], [Doc-3921], [Doc-1052]"""

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # Sidebar with chat options
    with st.sidebar:
        st.markdown("### Chat Options")
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        if st.button("💾 Save Conversation"):
            st.success("Conversation saved!")
        if st.button("📥 Load Context"):
            st.info("Context loaded from knowledge base")

elif page == "🔗 Graph Visualization":
    st.markdown('<h1 class="main-header">Neo4j Knowledge Graph</h1>', unsafe_allow_html=True)

    # Graph controls
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        node_type = st.selectbox("Node Type", ["All", "Person", "Document", "Concept", "Organization"])
    with col2:
        depth = st.slider("Depth", 1, 5, 2)
    with col3:
        layout = st.selectbox("Layout", ["Force-directed", "Circular", "Hierarchical", "Random"])
    with col4:
        max_nodes = st.number_input("Max Nodes", 10, 500, 100)

    # Search bar
    search = st.text_input("🔍 Search nodes...", placeholder="Enter node name or property...")

    st.markdown("---")

    # Create sample graph
    if st.button("🔄 Generate Graph") or st.session_state.graph_data is None:
        # Create a sample graph without networkx
        num_nodes = min(max_nodes, 50)

        # Generate node positions based on layout
        node_x = []
        node_y = []

        if layout == "Circular":
            # Circular layout
            for i in range(num_nodes):
                angle = 2 * math.pi * i / num_nodes
                node_x.append(math.cos(angle))
                node_y.append(math.sin(angle))
        elif layout == "Hierarchical":
            # Simple hierarchical layout
            levels = 4
            nodes_per_level = num_nodes // levels
            for i in range(num_nodes):
                level = i // nodes_per_level
                pos_in_level = i % nodes_per_level
                node_x.append(pos_in_level * 2.0 / nodes_per_level - 1)
                node_y.append(1 - level * 2.0 / levels)
        elif layout == "Force-directed":
            # Simulated force-directed layout (simplified)
            np.random.seed(42)
            node_x = np.random.randn(num_nodes) * 2
            node_y = np.random.randn(num_nodes) * 2
            # Simple spreading
            for _ in range(10):
                for i in range(num_nodes):
                    for j in range(i + 1, num_nodes):
                        dx = node_x[i] - node_x[j]
                        dy = node_y[i] - node_y[j]
                        dist = math.sqrt(dx * dx + dy * dy) + 0.01
                        if dist < 1:
                            force = (1 - dist) * 0.05
                            node_x[i] += dx / dist * force
                            node_y[i] += dy / dist * force
                            node_x[j] -= dx / dist * force
                            node_y[j] -= dy / dist * force
        else:  # Random
            node_x = np.random.randn(num_nodes)
            node_y = np.random.randn(num_nodes)

        # Create edges (random connections)
        edges = []
        edge_x = []
        edge_y = []

        # Generate random edges
        for i in range(num_nodes):
            # Each node connects to 1-4 other nodes
            num_connections = random.randint(1, min(4, num_nodes - 1))
            for _ in range(num_connections):
                j = random.randint(0, num_nodes - 1)
                if i != j and (i, j) not in edges and (j, i) not in edges:
                    edges.append((i, j))
                    edge_x.extend([node_x[i], node_x[j], None])
                    edge_y.extend([node_y[i], node_y[j], None])

        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='rgba(125, 125, 125, 0.5)'),
            hoverinfo='none',
            mode='lines')

        # Create node trace
        node_text = []
        node_color = []

        node_types = ['Person', 'Document', 'Concept', 'Organization']
        type_colors = {'Person': '#4fc3f7', 'Document': '#4caf50',
                       'Concept': '#ff9800', 'Organization': '#9c27b0'}

        for i in range(num_nodes):
            n_type = random.choice(node_types)
            node_text.append(f"{n_type}_{i}")
            node_color.append(type_colors[n_type])

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=False,
                color=node_color,
                size=15,
                line_width=2))

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=0),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            template='plotly_dark',
                            height=600,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        ))

        st.plotly_chart(fig, use_container_width=True)
        st.session_state.graph_data = fig
    else:
        st.plotly_chart(st.session_state.graph_data, use_container_width=True)

    # Graph statistics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nodes", f"{random.randint(80, 120)}")
    with col2:
        st.metric("Edges", f"{random.randint(150, 250)}")
    with col3:
        st.metric("Clusters", f"{random.randint(3, 7)}")
    with col4:
        st.metric("Density", f"{random.uniform(0.3, 0.7):.3f}")

    # Query builder
    with st.expander("🔧 Cypher Query Builder"):
        query = st.text_area("Enter Cypher Query",
                             value="MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25",
                             height=100)
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("▶️ Execute"):
                st.success("Query executed successfully!")
        with col2:
            if st.button("📋 Copy"):
                st.info("Query copied to clipboard!")

elif page == "📊 Metrics":
    st.markdown('<h1 class="main-header">Performance Metrics</h1>', unsafe_allow_html=True)

    # Time range selector
    col1, col2 = st.columns([3, 1])
    with col1:
        date_range = st.date_input("Select Date Range",
                                   value=(datetime.now() - timedelta(days=30), datetime.now()),
                                   format="YYYY-MM-DD")
    with col2:
        refresh = st.button("🔄 Refresh Metrics")

    st.markdown("---")

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Response Time", "0.34s", "-12%", help="Average query response time")
    with col2:
        st.metric("Success Rate", "94.2%", "+2.1%", help="Percentage of successful queries")
    with col3:
        st.metric("Active Sessions", "127", "+15", help="Current active user sessions")
    with col4:
        st.metric("Error Rate", "0.8%", "-0.3%", help="Percentage of failed requests")

    st.markdown("---")

    # Detailed metrics
    tab1, tab2, tab3, tab4 = st.tabs(["Performance", "Usage", "Errors", "Resources"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Response Time Distribution")
            response_times = np.random.lognormal(0, 0.5, 1000)
            fig = go.Figure(data=[go.Histogram(x=response_times, nbinsx=30,
                                               marker_color='#4fc3f7')])
            fig.update_layout(template='plotly_dark', height=300,
                              xaxis_title="Response Time (s)",
                              yaxis_title="Frequency")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Throughput Over Time")
            hours = list(range(24))
            throughput = [random.randint(800, 1200) + i * 10 for i in hours]
            fig = go.Figure(data=[go.Bar(x=hours, y=throughput,
                                         marker_color='#4caf50')])
            fig.update_layout(template='plotly_dark', height=300,
                              xaxis_title="Hour of Day",
                              yaxis_title="Requests/Hour")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("API Usage Statistics")
        endpoints = pd.DataFrame({
            'Endpoint': ['/search', '/analyze', '/graph', '/upload', '/export'],
            'Calls': [15234, 8921, 6547, 3210, 1876],
            'Avg Time (ms)': [234, 567, 890, 123, 456],
            'Success Rate': ['99.2%', '97.8%', '95.3%', '99.9%', '98.1%']
        })
        st.dataframe(endpoints, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Error Analysis")
        error_types = pd.DataFrame({
            'Error Type': ['Timeout', 'Bad Request', 'Server Error', 'Not Found', 'Auth Failed'],
            'Count': [45, 123, 12, 67, 23],
            'Percentage': ['16.7%', '45.6%', '4.4%', '24.8%', '8.5%']
        })

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(error_types, use_container_width=True, hide_index=True)
        with col2:
            fig = go.Figure(data=[go.Pie(labels=error_types['Error Type'],
                                         values=error_types['Count'],
                                         hole=0.4)])
            fig.update_layout(template='plotly_dark', height=250, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("System Resources")
        col1, col2 = st.columns(2)
        with col1:
            cpu_usage = [random.randint(40, 80) for _ in range(60)]
            fig = go.Figure(data=[go.Scatter(y=cpu_usage, mode='lines',
                                             line=dict(color='#ff9800', width=2))])
            fig.update_layout(template='plotly_dark', height=250,
                              title="CPU Usage (%)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            memory_usage = [random.randint(50, 70) for _ in range(60)]
            fig = go.Figure(data=[go.Scatter(y=memory_usage, mode='lines',
                                             line=dict(color='#9c27b0', width=2))])
            fig.update_layout(template='plotly_dark', height=250,
                              title="Memory Usage (%)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

elif page == "📁 File Upload":
    st.markdown('<h1 class="main-header">Model Training Data Upload</h1>', unsafe_allow_html=True)

    # Upload configuration
    col1, col2, col3 = st.columns(3)
    with col1:
        upload_type = st.selectbox("Upload Type",
                                   ["Training Data", "Validation Data", "Test Data", "Knowledge Base"])
    with col2:
        model_version = st.selectbox("Target Model",
                                     ["RAG Model v2.0", "Classification v1.5", "NER v3.0", "Custom"])
    with col3:
        preprocessing = st.selectbox("Preprocessing",
                                     ["Auto-detect", "Text Cleaning", "Tokenization", "None"])

    st.markdown("---")

    # File upload area
    uploaded_files = st.file_uploader(
        "Choose files for model training or term parsing",
        type=['csv', 'json', 'txt', 'pdf', 'xlsx'],
        accept_multiple_files=True,
        help="Upload data or term files. For term parsing, use .txt or .json with comma-separated words."
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")

        # File details
        st.subheader("📋 Uploaded Files")
        file_data = []
        for file in uploaded_files:
            file_data.append({
                'File Name': file.name,
                'Type': file.type,
                'Size': f"{file.size / 1024:.2f} KB",
                'Status': '✅ Ready'
            })
            st.session_state.uploaded_files.append(file)

        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # =========================================================
        # 🔄 New Section: Send Uploaded File to Backend (Safe Insert)
        # =========================================================
        st.markdown("### 🔄 Send to Backend for Term Processing")
        if st.button("🚀 Send to Backend"):
            for file in uploaded_files:
                try:
                    # Parse uploaded file
                    if file.name.endswith(".json"):
                        data = json.load(file)
                    else:
                        content = file.read().decode("utf-8")
                        terms = [t.strip() for t in content.split(",") if t.strip()]
                        data = {"terms": terms}

                    st.info(f"📤 Sending {file.name} with {len(data['terms'])} terms...")

                    # Backend endpoint (update if needed)
                    response = requests.post(
                        "http://127.0.0.1:8000/parse_terms",
                        json=data,
                        timeout=10
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Backend processed successfully!")
                        st.json(result)
                    else:
                        st.error(f"❌ Backend error {response.status_code}: {response.text}")

                except Exception as e:
                    st.error(f"⚠️ Error sending {file.name}: {e}")

        # =========================================================
        # Original Processing Options (Untouched)
        # =========================================================
        st.markdown("---")
        st.subheader("⚙️ Processing Options")

        col1, col2 = st.columns(2)
        with col1:
            batch_size = st.number_input("Batch Size", 16, 256, 32)
            validation_split = st.slider("Validation Split", 0.1, 0.3, 0.2)
            shuffle = st.checkbox("Shuffle Data", value=True)

        with col2:
            augmentation = st.checkbox("Data Augmentation", value=False)
            normalize = st.checkbox("Normalize Features", value=True)
            remove_duplicates = st.checkbox("Remove Duplicates", value=True)

        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            col1, col2 = st.columns(2)
            with col1:
                encoding = st.selectbox("Text Encoding", ["UTF-8", "ASCII", "Latin-1"])
                delimiter = st.selectbox("CSV Delimiter", [",", ";", "\t", "|"])
            with col2:
                max_features = st.number_input("Max Features", 100, 10000, 1000)
                min_samples = st.number_input("Min Samples per Class", 1, 100, 10)

        # Action buttons
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("▶️ Start Training", type="primary"):
                with st.spinner("Processing files and starting training..."):
                    import time
                    time.sleep(2)
                st.success("🚀 Training job initiated! Job ID: TRN-2025-0847")
        with col2:
            if st.button("📊 Validate Data"):
                st.info("Data validation in progress...")
        with col3:
            if st.button("👁️ Preview Data"):
                st.info("Loading data preview...")
        with col4:
            if st.button("🗑️ Clear All"):
                st.session_state.uploaded_files = []
                st.rerun()

    else:
        # Drag and drop area
        st.info("📤 Drag and drop files here or click to browse")

    # =========================================================
    # Original Recent Uploads Section (Untouched)
    # =========================================================
    st.markdown("---")
    st.subheader("📜 Recent Training Jobs")

    jobs_data = pd.DataFrame({
        'Job ID': ['TRN-2025-0846', 'TRN-2025-0845', 'TRN-2025-0844', 'TRN-2025-0843'],
        'Model': ['RAG Model v2.0', 'Classification v1.5', 'NER v3.0', 'RAG Model v1.9'],
        'Files': [12, 8, 15, 10],
        'Status': ['🟢 Completed', '🔵 Running', '🟢 Completed', '🔴 Failed'],
        'Accuracy': ['94.2%', 'Processing...', '91.8%', 'N/A'],
        'Duration': ['2h 15m', '1h 30m', '3h 45m', '0h 45m']
    })

    st.dataframe(jobs_data, use_container_width=True, hide_index=True)

    # Training metrics visualization
    if st.checkbox("Show Training Metrics"):
        col1, col2 = st.columns(2)
        with col1:
            epochs = list(range(1, 21))
            loss = [3.5 - i * 0.15 + random.uniform(-0.1, 0.1) for i in epochs]
            fig = go.Figure(data=[go.Scatter(x=epochs, y=loss, mode='lines+markers',
                                             line=dict(color='#ff5252', width=2))])
            fig.update_layout(template='plotly_dark', height=300,
                              title="Training Loss", xaxis_title="Epoch", yaxis_title="Loss")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            accuracy = [0.5 + i * 0.02 + random.uniform(-0.01, 0.01) for i in epochs]
            fig = go.Figure(data=[go.Scatter(x=epochs, y=accuracy, mode='lines+markers',
                                             line=dict(color='#4caf50', width=2))])
            fig.update_layout(template='plotly_dark', height=300,
                              title="Validation Accuracy", xaxis_title="Epoch", yaxis_title="Accuracy")
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; padding: 1rem;'>
        <small>Frederick Platform v2.0.1 | Powered by RAG & Neo4j | © 2025 Frederick AI</small>
    </div>
    """,
    unsafe_allow_html=True
)
