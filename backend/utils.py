# Source: https://neo4j.com/docs/python-manual/current/connect/
from neo4j import GraphDatabase

uri = "bolt://fnl-llm-neo4j.tdm.geddes.rcac.purdue.edu:7687/"
auth = ("neo4j", "trunk-SCREEN-loud-orange-8910")

#uri = "bolt://localhost:7687"
#auth = ("neo4j", "neo4j")
#username = "neo4j"  # Replace with your Neo4j username
#password = "neo4j"  # Replace with your Neo4j password
#driver = GraphDatabase.driver(uri, auth=(username, password))

# Establish a connection
with GraphDatabase.driver(uri, auth=auth) as driver:
    driver.verify_connectivity()
    print("Connection established.")


driver = GraphDatabase.driver(uri, auth=auth)

# Classes for term and code matches
class get_node_match:
    def __init__(self):
        #self.name = name  # Instance attribute
        pass


    def get_exact_match_from_code(self, code):
        # Execute a query
        with driver.session() as session:
            # Use parameters for safe and correct handling of values
            query = """
            MATCH (n)
            WHERE n.code = $target_code
            RETURN n
            LIMIT 1
            """
            # Pass parameters as a dictionary to session.run
            result = session.run(query, target_code=f"{code}")
    
            for record in result:
                r = record["n"] # Access the returned node using the variable name 'n'
                
                print("element_id= ", r.element_id, "\nlabels= ", r.labels, "\ncode: ", r.get("code"), "\ntype: ", r.get("type"))
                
                return {
                    'code': r.get('code'),
                    'origin': r.get('origin'),
                    'type': r.get('type'),
                    'term': r.get('term'),
                    'definition': r.get('definition'),
                    'nomic_embedding': r.get('nomic_embedding'),
                    'openai_embedding': r.get('openai_embedding'),
                    'embedding': r.get('embedding'),
                    'element_id': r.element_id,
                    'labels': r.labels
                }


    def get_exact_match_from_term(self, term):
        # Execute a query
        with driver.session() as session:
            # Use parameters for safe and correct handling of values
            query = """
            MATCH (n)
            WHERE n.term = $target_term
            RETURN n
            LIMIT 1
            """
            # Pass parameters as a dictionary to session.run
            result = session.run(query, target_term=f"{term}")
    
            for record in result:
                r = record["n"] # Access the returned node using the variable name 'n'
                
                print("element_id= ", r.element_id, "\nlabels= ", r.labels, "\ncode: ", r.get("code"), "\ntype: ", r.get("type"))
                
                return {
                    'code': r.get('code'),
                    'origin': r.get('origin'),
                    'type': r.get('type'),
                    'term': r.get('term'),
                    'definition': r.get('definition'),
                    'nomic_embedding': r.get('nomic_embedding'),
                    'openai_embedding': r.get('openai_embedding'),
                    'embedding': r.get('embedding'),
                    'element_id': r.element_id,
                    'labels': r.labels
                }


class get_synonyms:
    def __init__(self, name):
        pass


    def find_by_code(self, code):
        pass


    def find_by_term(self, term):
        pass


class SemanticSearcher:
    def __init__(self, name):
        pass


    def semantic_pv_search(self, code):
        pass


    def semantic_ncit_search(self, term):
        pass

# Close the driver connection
#driver.close()