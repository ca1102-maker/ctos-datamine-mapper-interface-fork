# mock_backend.py (for neo4j)
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

def load_graph_data(file_path="graph_data.txt"):
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
    Example endpoint: http://127.0.0.1:8000/graph_data
    """
    try:
        data = load_graph_data("graph_data.txt")
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
