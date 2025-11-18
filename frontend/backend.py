# backend.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import os
import traceback

# =========================
# 1) Environment & OpenAI
# =========================
load_dotenv()  # reads .env in same folder
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("⚠️ ERROR: OPENAI_API_KEY not found in .env file!")
    client = None
else:
    print("✅ OpenAI key loaded successfully.")
    client = OpenAI(api_key=api_key)

# =========================
# 2) FastAPI app + CORS
# =========================
app = FastAPI(title="Frederick Unified Backend API")

# Allow Streamlit frontend & others to reach this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 3) ChatGPT endpoint: /chat
# =========================
@app.post("/chat")
async def chat_with_gpt(request: Request):
    """
    Receives:
      {
        "message": "...",
        "mode": "general" | "graph" (optional),
        "graph_context": { "nodes": [...], "edges": [...] } (optional)
      }
    Returns:
      { "reply": "..." }
    """
    try:
        body = await request.json()
        print("📥 /chat body from frontend:", body)

        user_message = (body.get("message") or "").strip()
        mode = body.get("mode", "general")
        graph_context = body.get("graph_context")

        if not user_message:
            return JSONResponse({"error": "Empty message"}, status_code=400)

        if client is None:
            return JSONResponse(
                {"error": "OpenAI client not initialized (missing API key)."},
                status_code=500,
            )

        # --- Build system prompt depending on mode ---
        if mode == "graph" and graph_context:
            system_prompt = (
                "You are an AI assistant that helps explain and explore a biomedical term graph. "
                "You receive nodes and edges representing terms and similarity scores between them. "
                "You can:\n"
                "- Explain relationships between terms\n"
                "- Suggest which terms are most central or related\n"
                "- Talk about the structure of the graph based on the context.\n"
                "Do NOT make up nodes that are not in the provided context."
            )
        else:
            system_prompt = (
                "You are a helpful biomedical AI assistant answering user questions clearly and concisely."
            )

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Optionally include a compact summary of the graph context
        if mode == "graph" and graph_context:
            nodes = graph_context.get("nodes", [])
            edges = graph_context.get("edges", [])
            summary_text = (
                f"The current graph has {len(nodes)} nodes and {len(edges)} edges. "
                f"Nodes include: {', '.join(list(nodes)[:15])}"
            )
            messages.append({"role": "system", "content": summary_text})

        # User message
        messages.append({"role": "user", "content": user_message})

        # --- Call OpenAI without response_format (plain text reply) ---
        completion = client.chat.completions.create(
            model="gpt-4o-mini",   # or "gpt-4-turbo"
            messages=messages,
        )

        reply = completion.choices[0].message.content
        print("🤖 GPT reply:", reply[:200], "...")
        return JSONResponse({"reply": reply})

    except Exception as e:
        print("❌ ERROR during /chat request:")
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


# =========================
# 4) Term parsing endpoint: /parse_terms
# =========================
@app.post("/parse_terms")
async def parse_terms(request: Request):
    """
    Receives {"terms": [...]} from the File Upload page in Streamlit,
    returns a mock clustering of terms.
    """
    try:
        data = await request.json()
        terms = data.get("terms", [])

        print("📥 /parse_terms received terms:", terms)

        sorted_terms = sorted(terms)
        mid = len(sorted_terms) // 2
        clusters = [
            {"cluster_id": 1, "terms": sorted_terms[:mid]},
            {"cluster_id": 2, "terms": sorted_terms[mid:]},
        ]

        return {
            "status": "success",
            "received_terms": terms,
            "total_terms": len(terms),
            "clusters": clusters,
        }

    except Exception as e:
        print("❌ ERROR during /parse_terms request:")
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

# =========================
# 5) Graph data endpoint: /graph_data
# =========================
def load_graph_data(file_path: str = "graph_data.txt"):
    nodes = set()
    edges = []
    with open(file_path, "r") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            term1, term2, score = [x.strip() for x in line.split(",")]
            edges.append({
                "source": term1,
                "target": term2,
                "similarity": float(score)
            })
            nodes.update([term1, term2])
    return {"nodes": [{"name": n} for n in nodes], "edges": edges}

@app.get("/graph_data")
def get_graph_data():
    """
    Returns nodes and edges for visualization.
    Example: http://127.0.0.1:8000/graph_data
    """
    try:
        data = load_graph_data("graph_data.txt")
        print("📡 /graph_data served", len(data["nodes"]), "nodes and", len(data["edges"]), "edges")
        return JSONResponse(content=data)
    except Exception as e:
        print("❌ ERROR during /graph_data request:")
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

# =========================
# 6) Local dev entrypoint
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
