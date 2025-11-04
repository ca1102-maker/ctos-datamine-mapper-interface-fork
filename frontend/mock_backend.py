# soham, chris -- mock file testing backend file 
# accepts file, reads json, then return them accordingly.

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Mock Term Parser API")

# Allow frontend (Streamlit) to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/parse_terms")
async def parse_terms(request: Request):
    data = await request.json()
    terms = data.get("terms", [])

    # Simulated backend logic (mock clustering)
    sorted_terms = sorted(terms)
    clusters = [
        {"cluster_id": 1, "terms": sorted_terms[:len(sorted_terms)//2]},
        {"cluster_id": 2, "terms": sorted_terms[len(sorted_terms)//2:]}
    ]

    return {
        "status": "success",
        "received_terms": terms,
        "total_terms": len(terms),
        "clusters": clusters
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
