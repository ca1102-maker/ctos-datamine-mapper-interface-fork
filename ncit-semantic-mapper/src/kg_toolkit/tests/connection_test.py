from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()

def test_connection(uri, username, password):
    """
    Connects to the Neo4j database and runs a simple query.
    Prints the result and returns True on success, False on failure.
    """
    driver = None  # Ensure driver is defined in case of connection error
    try:
        # Check if credentials were loaded correctly
        if not all([uri, username, password]):
            print("Error: Missing one or more Neo4j credentials (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD).")
            print("Please ensure they are set in your .env file.")
            return False

        print(f"Attempting to connect to Neo4j at {uri}...")
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful!' AS message")
            print(f"-> {result.single()['message']}")
        
        return True
    
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    
    finally:
        if driver:
            driver.close()
            print("Driver connection closed.")

# This block allows the script to be run directly from the command line
if __name__ == "__main__":
    print("--- Running Neo4j Connection Test ---")
    
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")    
    
    test_connection(uri, username, password)
    
    print("--- Test Finished ---")