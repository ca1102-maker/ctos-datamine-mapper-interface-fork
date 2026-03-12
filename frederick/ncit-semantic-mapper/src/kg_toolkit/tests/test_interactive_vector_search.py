#!/usr/bin/env python3
"""
Interactive Vector Search Test Script for the KG-Toolkit.

This script allows a user to provide a text prompt and perform a
vector similarity search against the configured Neo4j database.
"""

import os
import sys
from dotenv import load_dotenv

from kg_toolkit.semantic_retrievers import SemanticSearcher

try:
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
except Exception as e:
    print(f"Warning: Could not load .env file. Ensure credentials are set in your environment. Error: {e}")


def print_results(results, search_term, index_name):
    """Formats and prints the search results in a readable way."""
    print("\n" + "=" * 80)
    print(f"Search Results for '{search_term}' in index '{index_name}'")
    print("=" * 80)

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        metadata = result.get('metadata', {})
        score = metadata.get('score', 0.0)
        
        print(f"\nResult {i} (Similarity Score: {score:.4f})")
        
        # Display key fields from the metadata
        identifier = metadata.get('cde_term') or metadata.get('concept_term') or metadata.get('pv_term', 'N/A')
        code = metadata.get('cde_code') or metadata.get('concept_code') or metadata.get('pv_code', 'N/A')
        definition = metadata.get('cde_definition') or metadata.get('concept_definition') or result.get('text', '')

        print(f"   Term: {identifier} (Code: {code})")
        
        # Truncate long definitions for cleaner display
        if definition and len(definition) > 150:
            definition = definition[:147] + "..."
        print(f"   Definition: {definition}")
    print()


def main():
    """Main function to run the interactive test session."""
    print("--- Interactive Vector Search Test ---")
    
    searcher = None
    try:
        print("\nInitializing Semantic Searcher (connecting to Neo4j and Ollama)...")
        # The SemanticSearcher class now loads from .env by default
        searcher = SemanticSearcher()
        print("Initialization successful!")
        
        while True:
            print("\n" + "-" * 60)
            
            # 1. Get the search term from the user
            search_term = input("Enter a search term or description (or 'quit' to exit): ").strip()
            if search_term.lower() in ['quit', 'exit', 'q']:
                break
            if not search_term:
                print("Search term cannot be empty.")
                continue

            # 2. Get the index to search
            print("\nWhich vector index would you like to search?")
            print("  1. NCIT Index (for medical concepts)")
            print("  2. CDE Index (for common data elements)")
            print("  3. PV Index (for permissible values)")
            choice = input("Enter your choice (1, 2, or 3): ").strip()
            
            # 3. Get the number of results
            try:
                limit_str = input("How many results to return? (default: 3): ").strip()
                limit = int(limit_str) if limit_str else 3
            except ValueError:
                limit = 3

            print("\nSearching...")
            
            results = []
            index_name = ""
            # 4. Call the appropriate search method
            if choice == '1':
                index_name = "ncitIndex"
                results = searcher.find_ncit_by_definition_similarity(search_term, top_k=limit)
            elif choice == '2':
                index_name = "cdeIndex"
                results = searcher.find_cde_by_definition_similarity(search_term, top_k=limit)
            elif choice == '3':
                index_name = "pvIndex"
                results = searcher.find_cde_from_pv_term(search_term, top_k=limit)
            else:
                print("Invalid choice. Please try again.")
                continue

            # 5. Display the results
            print_results(results, search_term, index_name)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure your Neo4j and Ollama servers are running and configured in the .env file.")
    finally:
        if searcher and hasattr(searcher, 'close'):
            searcher.close()
            print("\nDatabase connection closed. Goodbye!")

if __name__ == "__main__":
    main()