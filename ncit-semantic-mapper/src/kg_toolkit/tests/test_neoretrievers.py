import pytest
import json

from kg_toolkit.utils.search_engine import Neo4jRetriever, FullTextNeo4jRetriever

def test_keyword_retriever(graph):
    """
    Tests the basic Neo4jRetriever which performs a keyword search.
    
    Args:
        graph: The Neo4jGraph fixture from conftest.py.
    """
    # The 'graph' fixture is automatically passed in, no need for 'graph = graph'
    retr = Neo4jRetriever(
        graph=graph,
        node_label="CDE",
        k=5,
        text_node_properties=['term', 'code'],
        metadata_properties=['type']
    )
    
    # This retriever likely does a "match all", so the input query doesn't matter.
    resp = retr.invoke('dummy') 
    
    assert len(resp) == 5, "The retriever should return k=5 documents."
    assert json.loads(resp[0].page_content), "The page_content should be a valid JSON string."
    assert resp[0].metadata['type'] == 'CDE', "The metadata 'type' should be 'CDE'."

def test_full_text_retriever(graph):
    """
    Tests the FullTextNeo4jRetriever against a specific full-text index.
    
    Args:
        graph: The Neo4jGraph fixture from conftest.py.
    """
    retr = FullTextNeo4jRetriever(
        graph=graph,
        index_name="ftTermIndex", # This index must exist on the database for this test to pass
        node_label="Term",
        k=3,
        text_node_properties=['term', 'code'],
        metadata_properties=['code', 'type']
    )
    
    resp = retr.invoke("cachexia")
    
    assert len(resp) <= 3, "The retriever should return at most k=3 documents."
    
    if resp: # Only run these checks if any results were returned
        assert 'score' in resp[0].metadata, "Full-text results should include a 'score' in their metadata."
        # This check is broad but confirms the index is searching across multiple node types as expected.
        assert resp[0].metadata['type'] in ('VDM', 'CDE', 'NCIT', 'PV', 'Term'), "The result type is not one of the expected types."

@pytest.mark.skip(reason="This test is a placeholder and has not been implemented yet.")
def test_siretrievers():
    """
    A placeholder for a future test.
    Using pytest.mark.skip to prevent it from running and causing errors.
    """
    pass