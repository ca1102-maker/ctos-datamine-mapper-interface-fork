import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ncit-semantic-mapper'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core_tools.semantic_retrievers import SemanticSearcher
from core_tools.exact_match import get_node_match
from core_tools.synonym_tool import get_synonyms

app = FastAPI()

# models: defines the attributes and properties of a specific resource.
class CodeQuery(BaseModel):
    code: str

class TermQuery(BaseModel):
    term: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Frontend can differentiate between code and term submission before sending a request
# to the backend, so separate input boxes aren't necessary.
@app.post("/exact_match/by_code")
def exact_match_by_code(query: CodeQuery):
    matcher = get_node_match()
    result = matcher.get_exact_match_from_code(query.code)
    if not result:
        raise HTTPException(status_code=404, detail="No exact match found for code")
    return result

@app.post("/exact_match/by_term")
def exact_match_by_term(query: TermQuery):
    matcher = get_node_match()
    result = matcher.get_exact_match_from_term(query.term)
    if not result:
        raise HTTPException(status_code=404, detail="No exact match found for term")
    return result

@app.post("/synonym/by_code")
def synonym_by_code(query: CodeQuery):
    result = get_synonyms().find_by_code(query.code)
    if not result:
        raise HTTPException(status_code=404, detail="No synonyms found for code")
    return result

@app.post("/synonym/by_term") # or PV according to the ncit-semantic-mapper
def synonym_by_term(query: TermQuery):
    result = get_synonyms().find_by_term(query.term)
    if not result:
        raise HTTPException(status_code=404, detail="No synonyms found for term")
    return result

@app.post("semantic/by_code")
def semantic_by_code(query: CodeQuery):
    searcher = SemanticSearcher()
    result = searcher.semantic_pv_search(query.code)
    if not result:
        raise HTTPException(status_code=404, detail="No semantic PV matches found")
    return result

@app.post("semantic/by_term")
def semantic_by_term(query: TermQuery):
    searcher = SemanticSearcher()
    result = searcher.semantic_ncit_search(query.term)
    if not result:
        raise HTTPException(status_code=404, detail="No semantic NCIT matches found")
    return result
