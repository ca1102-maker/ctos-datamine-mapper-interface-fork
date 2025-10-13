import os
from .config import Config
from neo4j import GraphDatabase
from langchain_ollama.embeddings import OllamaEmbeddings 

class SemanticSearcher:
    """
    Performs semantic search using a local Nomic model served by Ollama.
    """
    def __init__(self, uri = Config.NEO4J_URI,
                 username = Config.NEO4J_USERNAME,
                 password = Config.NEO4J_PASSWORD):
        
        self.embedding_client = OllamaEmbeddings(model="nomic-embed-text")
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def get_embedding(self, text: str) -> list[float]:
        """
        Convert text to an embedding vector using the local nomic-embed-text model.
        """
        try:
            # Use the embed_query method for single text inputs
            return self.embedding_client.embed_query(text)
        except Exception as e:
            print(f"Error generating Nomic embedding with Ollama: {e}")
            return None
    
    def find_cde_from_pv_term(self, pv_term: str, top_k: int = 5):
        """
        Search for CDEs by finding similar PV terms using semantic search.
        
        Args:
            pv_term (str): The permissible value term to search for.
            top_k (int): Number of top results to return.
            
        Returns:
            List of dictionaries containing PV and CDE information.
        """
        embedding = self.get_embedding(pv_term)
        if not embedding:
            return []
        
        query = """
        CALL db.index.vector.queryNodes('pvIndex', $top_k, $embedding) 
        YIELD node, score
        WHERE node:PV
        WITH node, score
        MATCH (node)<-[:HAS_PV]-(vdm:VDM)<-[:HAS_VDM]-(cde:CDE)
        RETURN node.definition as text, score,
               {score: score, 
                pv_code: node.code, 
                pv_term: node.term,
                cde: cde.code, 
                cde_term: cde.term, 
                cde_defn: cde.definition} as metadata
        ORDER BY score DESC
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(query, top_k=top_k, embedding=embedding)
                return [record.data() for record in result]
            except Exception as e:
                print(f"Error executing PV to CDE search: {e}")
                return []
    
    def find_cde_from_ncit_term(self, ncit_term: str, top_k: int = 5):
        """
        Search for CDEs by finding similar NCIT concepts using semantic search.
        
        Args:
            ncit_term (str): The NCIT concept term to search for.
            top_k (int): Number of top results to return.
            
        Returns:
            List of dictionaries containing NCIT, PV, and CDE information.
        """
         embedding = self.get_embedding(ncit_term)
        if not embedding:
            return []
        
        query = """
        CALL db.index.vector.queryNodes('ncitIndex', $top_k, $embedding) 
        YIELD node, score
        WHERE node:NCIT
        WITH node, score
        MATCH (node)<-[:HAS_CONCEPT]-(pv:PV)
        OPTIONAL MATCH (pv)<-[:HAS_PV]-(vdm:VDM)<-[:HAS_VDM]-(cde:CDE)
        WITH collect(cde.code) as cdes, node, pv, score
        RETURN node.definition as text, score,
               {score: score, 
                concept_code: node.code, 
                concept_term: node.term,
                pv_code: pv.code, 
                pv_term: pv.term,
                of_cdes: cdes} as metadata
        ORDER BY score DESC
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(query, top_k=top_k, embedding=embedding)
                return [record.data() for record in result]
            except Exception as e:
                print(f"Error executing NCIT to CDE search: {e}")
                return []
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()