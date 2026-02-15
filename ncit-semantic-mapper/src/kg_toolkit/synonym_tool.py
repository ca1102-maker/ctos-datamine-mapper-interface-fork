"""
Simple Synonym Finder - Cancer Knowledge Graph
Fetches all synonym data for a given term, code or permissible value
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

class get_synonyms:
    """
    A class to get all synonym data for a given input term or permissible value.
    """
    def __init__(self, uri=None, username=None, password=None):
        """
        Initializes the connection to Neo4j.
        If credentials are not provided, it will attempt to load them from environment variables.
        """
        load_dotenv()
        self.uri = uri or os.getenv("NEO4J_URI")
        self.username = username or os.getenv("NEO4J_USERNAME")
        self.password = password or os.getenv("NEO4J_PASSWORD")

        if not all([self.uri, self.username, self.password]):
            raise ValueError("Neo4j credentials not provided or found in environment variables.")

        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        print("Synonym Finder connected to the database.")

    def close(self):
        """Closes the database driver connection."""
        if self.driver:
            self.driver.close()
            print("Synonym Finder database connection closed.")

    def get_synonyms_from_pv(self, pv: str) -> list[str]:
        """ 
        Finds synonyms for a permissible value using the PV -> NCIT -> SYN graph path.

        Args: 
            pv (str): The permissible value to search for (e.g., 'prostate').
        Returns:
            A list of synonym strings.
        """
        query = """
        MATCH (pv:PV {term: $pv})
        MATCH (pv)-[:HAS_CONCEPT]->(:NCIT)-[:HAS_SYNONYM]->(syn:SYN)
        RETURN syn.term AS synonym
        """
        
        print(f"Finding synonyms for PV: '{pv}'")
        try:
            with self.driver.session() as session:
                result = session.run(query, pv=pv)
                synonyms = [record["synonym"] for record in result]
            
            if not synonyms:
                print("-> No synonyms found.")
                return []
            
            print(f"-> Found {len(synonyms)} synonyms.")
            return synonyms
            
        except Exception as e:
            print(f"Query failed: {e}")
            return []

    def get_synonyms_from_termcode(self, code: str) -> list[str]:
        """
        Finds synonyms for a term using its NCIT code.
        
        Args: 
            code (str): The NCIT code for a term (e.g., 'C4878').
        Returns:
            A list of synonym strings.
        """
        query = """
        MATCH (n:NCIT {code: $code})-[:HAS_SYNONYM]->(syn:SYN)
        RETURN syn.term AS synonym
        """
        print(f"Finding synonyms for NCIT code: {code}")

        try:
            with self.driver.session() as session:
                result = session.run(query, code=code)
                synonyms = [record["synonym"] for record in result]
            
            if not synonyms:
                print(f"-> No synonyms found for NCIT code '{code}'.")
                return []
            
            print(f"-> Found {len(synonyms)} synonyms.")
            return synonyms
            
        except Exception as e:
            print(f"Query failed: {e}")
            return []