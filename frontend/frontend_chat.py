import streamlit as st
import requests

st.set_page_config(page_title="Team Chat Backend Test")

API_URL = "http://127.0.0.1:8000/parse_terms"

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🧠 Team Backend Chat Test")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Send message
if prompt := st.chat_input("Enter terms (comma-separated)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):

            try:
                terms = [t.strip() for t in prompt.split(",")]
                res = requests.post(API_URL, json={"terms": terms})
                data = res.json()

                reply = f"✅ Total Terms: {data['total_terms']}\n"
                for c in data["clusters"]:
                    reply += f"- Cluster {c['cluster_id']}: {', '.join(c['terms'])}\n"

            except Exception as e:
                reply = f"⚠️ Error: {str(e)}"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
