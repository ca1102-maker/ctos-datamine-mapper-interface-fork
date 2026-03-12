#!/usr/bin/env python3
import sys
import os
from dotenv import load_dotenv

# --- MODIFIED: Use the correct import path for the new project structure ---
from kg_toolkit.exact_match import get_node_match
# Load environment variables from the project root .env file
load_dotenv()

def get_search_type():
    """Gets user input for the desired search type."""
    while True:
        print("\nChoose search method:")
        print("1. Search by NCIT Code (Exact) - e.g., 'C40625'")
        print("2. Search by Term (Exact) - e.g., 'Lung Carcinoma'")
        print("3. Search by Term (Fuzzy) - e.g., 'lung'")
        print("4. Quit")
        choice = input("\nEnter your choice (1, 2, 3, or 4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return {'1': 'code', '2': 'term', '3': 'fuzzy', '4': 'quit'}[choice]
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

def search_by_code(matcher):
    """Handles the search-by-code workflow."""
    code = input("Enter an NCIT code to search for: ").strip().upper()
    if not code:
        print("Please enter a valid NCIT code.")
        return
    print()
    result = matcher.get_exact_match_from_code(code)
    print(f"\nResult for NCIT code '{code}': {f'Found {result}' if result else 'Not found'}")

def search_by_term(matcher):
    """Handles the exact-search-by-term workflow."""
    term = input("Enter a term to search for: ").strip()
    if not term:
        print("Please enter a valid term.")
        return
    print()
    result = matcher.get_exact_match_from_term(term)
    print(f"\nResult for term '{term}': {'Found' if result else 'Not found'}")

def fuzzy_search_by_term(matcher):
    """Handles the fuzzy-search-by-term workflow."""
    term = input("Enter a term to fuzzy search for: ").strip()
    if not term:
        print("Please enter a valid term.")
        return

    try:
        limit_str = input("How many results? (default: 5, max: 20): ").strip()
        limit = int(limit_str) if limit_str else 5
        if not 1 <= limit <= 20:
            print("Please enter a number between 1 and 20.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return
    
    print("\nPerforming full-text index search...")
    results = matcher.get_fuzzy_term_matches(term, limit=limit)
    
    if not results:
        print(f"No full-text matches found for term '{term}'.")
        return

    print(f"\nFound {len(results)} full-text matches for '{term}':")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Term: {result['term']} (Code: {result['code']})")
        definition = result.get('definition', 'Not available')
        print(f"   Definition: {(definition[:147] + '...') if len(definition) > 150 else definition}")

def main():
    """Main execution function."""
    print("=== Enhanced Node Matcher Test with Fuzzy Search ===")
    
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("Error: Missing required Neo4j environment variables (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD).")
        sys.exit(1)
    
    matcher = None
    try:
        print("\nConnecting to Neo4j database...")
        matcher = get_node_match(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        print("Connection successful!")
        
        while True:
            print("-" * 60)
            search_type = get_search_type()
            
            if search_type == 'quit':
                break
            elif search_type == 'code':
                search_by_code(matcher)
            elif search_type == 'term':
                search_by_term(matcher)
            elif search_type == 'fuzzy':
                fuzzy_search_by_term(matcher)
            
            print()
            continue_choice = input("Would you like to perform another search? (y/n): ").strip().lower()
            if continue_choice in ['n', 'no']:
                break
                
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if matcher and hasattr(matcher, 'close'):
            matcher.close()
        print("\nThanks for testing the Node Matcher!")

if __name__ == "__main__":
    main()