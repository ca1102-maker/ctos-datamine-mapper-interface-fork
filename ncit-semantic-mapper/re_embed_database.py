import os
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_ollama.embeddings import OllamaEmbeddings

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
MODEL_NAME = "nomic-embed-text"
NEW_EMBEDDING_PROPERTY = "nomic_embedding"
BATCH_SIZE = 50

if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    raise ValueError("Neo4j credentials not set in .env file. Please check your configuration.")

print(f"Initializing Ollama embeddings with model: '{MODEL_NAME}'")
embeddings_model = OllamaEmbeddings(model=MODEL_NAME)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def backfill_embeddings(session, node_label: str, text_property: str):
    """
    Fetches nodes missing the new embedding, generates embeddings for them,
    and writes the new embeddings back to the Neo4j database in batches.
    """
    print("\n" + "="*60)
    print(f"Starting backfill for nodes with label '{node_label}'")
    print(f"Using text from property: '{text_property}'")
    
    query_read = f"""
    MATCH (n:{node_label})
    WHERE n.{text_property} IS NOT NULL AND n.{NEW_EMBEDDING_PROPERTY} IS NULL
    RETURN elementId(n) AS elementId, n.{text_property} AS text
    """
    
    results = session.run(query_read)
    nodes_to_process = [(record["elementId"], record["text"]) for record in results]
    
    if not nodes_to_process:
        print(f"-> No nodes to update for label '{node_label}'. All nodes already have the '{NEW_EMBEDDING_PROPERTY}' property.")
        return

    total_nodes = len(nodes_to_process)
    print(f"-> Found {total_nodes} nodes to update.")
    start_time = time.time()

    for i in range(0, total_nodes, BATCH_SIZE):
        batch = nodes_to_process[i:i + BATCH_SIZE]
        element_ids = [item[0] for item in batch]
        texts = [item[1] for item in batch]
        
        new_embeddings = embeddings_model.embed_documents(texts)
        
        batch_data = [{"elementId": eid, "embedding": emb} for eid, emb in zip(element_ids, new_embeddings)]
        
        query_write = f"""
        UNWIND $batch_data AS data
        MATCH (n) WHERE elementId(n) = data.elementId
        SET n.{NEW_EMBEDDING_PROPERTY} = data.embedding
        """
        session.run(query_write, batch_data=batch_data)
        
        processed_count = i + len(batch)
        elapsed_time = time.time() - start_time
        avg_time_per_node = elapsed_time / processed_count if processed_count > 0 else 0
        estimated_remaining = (total_nodes - processed_count) * avg_time_per_node
        
        print(f"  Processed batch {i//BATCH_SIZE + 1} ({processed_count}/{total_nodes} nodes). "
              f"Estimated time remaining: {estimated_remaining:.2f} seconds.")

    total_time = time.time() - start_time
    print(f"-> Backfill for '{node_label}' complete. Total time: {total_time:.2f} seconds.")

def main():
    """Main function to control the re-embedding process for all relevant node labels."""
    print("Starting comprehensive Neo4j database re-embedding process...")
    try:
        with driver.session(database="neo4j") as session:
            
            backfill_embeddings(session, node_label="NCIT", text_property="definition")
            backfill_embeddings(session, node_label="PV", text_property="definition")
            backfill_embeddings(session, node_label="CDE", text_property="definition")
            backfill_embeddings(session, node_label="VDM", text_property="definition")
            backfill_embeddings(session, node_label="Term", text_property="definition")            
            print("\n" + "="*60)
            print("Database re-embedding process finished successfully!")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("Neo4j driver connection closed.")

if __name__ == "__main__":
    main()