"""
Simple Node Matcher - Knowledge Graph
Fetches exact matches for any term, code, label or concept, and supports fuzzy search.
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

class get_node_match:
    """
    A class to get full node details for an exact or fuzzy match from the Neo4j database.
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
        print("Node Matcher connected to the database.")

    def close(self):
        """Closes the database driver connection."""
        if self.driver:
            self.driver.close()
            print("Node Matcher database connection closed.")

    def get_exact_match_from_code(self, code):
        """
        Retrieves node details by an exact match on the code.
        """
        # --- MODIFIED: Changed 'openai_embedding' to 'nomic_embedding' ---
        query = """
        MATCH (n:NCIT {code: $code})
        RETURN n.term as term, 
               n.definition as definition, 
               n.type as type, 
               n.nomic_embedding as embedding
        """
        
        print(f"Finding exact match for code: {code}")
        try:
            with self.driver.session() as session:
                result = session.run(query, code=code)
                record = result.single()
                
                if not record:
                    print(f"No exact match found for code '{code}'")
                    return None
                
                node_data = dict(record)
                node_data['code'] = code # Add the code to the returned data
                print("Exact match found!")
                return node_data
                
        except Exception as e:
            print(f"Query failed: {e}")
            return None
    
    def get_exact_match_from_term(self, term):
        """
        Retrieves node details by a case-insensitive exact match on the term name.
        """
        normalized_term = term.strip()
        # --- MODIFIED: Changed 'openai_embedding' to 'nomic_embedding' ---
        query = """
        MATCH (n:NCIT)
        WHERE toLower(n.term) = toLower($term)
        RETURN n.code as code,
               n.term as term, 
               n.definition as definition, 
               n.type as type, 
               n.nomic_embedding as embedding
        LIMIT 1
        """
        
        print(f"Finding exact match for term: '{term}'")
        try:
            with self.driver.session() as session:
                result = session.run(query, term=normalized_term)
                record = result.single()
                
                if not record:
                    print(f"No exact match found for term '{term}'")
                    return None
                
                node_data = dict(record)
                print("Exact match found!")
                return node_data
                
        except Exception as e:
            print(f"Query failed: {e}")
            return None

    def get_fuzzy_term_matches(self, term, limit=5):
        """
        Gets multiple potential matches for a term using a full-text index.
        """
        print(f"Finding fuzzy matches for term: '{term}'")
        try:
            with self.driver.session() as session:
                index_name = 'ftTermIndex'
                search_query = f"""
                CALL db.index.fulltext.queryNodes($index_name, $term)
                YIELD node, score
                WHERE node:NCIT
                RETURN node.code as code,
                       node.term as term,
                       node.definition as definition,
                       node.type as type,
                       score
                ORDER BY score DESC
                LIMIT $limit
                """
                
                result = session.run(search_query, index_name=index_name, term=term, limit=limit)
                matches = [dict(record) for record in result]
                
                print(f"Found {len(matches)} fuzzy matches.")
                return matches
                
        except Exception as e:
            if "No such index" in str(e):
                print(f"Fuzzy search failed: Full-text index '{index_name}' not found on the database.")
            else:
                print(f"Fuzzy search failed: {e}")
            return []