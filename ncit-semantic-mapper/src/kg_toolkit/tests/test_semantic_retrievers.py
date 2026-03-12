#!/usr/bin/env python3
"""
Interactive Semantic Search Tool for SI-Tamer Database

This script provides an interactive command-line interface for searching
the semantic infrastructure database using PV, NCIT, and definition similarity searches.
"""

import os
from dotenv import load_dotenv
from kg_toolkit.semantic_retrievers import SemanticSearcher
try:
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
except Exception as e:
    print(f"Warning: Could not load .env file. Ensure credentials are set in your environment. Error: {e}")
    
def print_separator():
    """Prints a consistent separator line."""
    print("=" * 80)

def print_results(results, title, search_term):
    """Generic function to format and print search results."""
    print_separator()
    print(f"{title} for: '{search_term}' (Found {len(results)} results)")
    print_separator()

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        metadata = result.get('metadata', {})
        score = metadata.get('score', 0.0)
        print(f"\nResult {i} (Similarity Score: {score:.4f})")
        
        # Dynamically print available fields from metadata
        for key, value in metadata.items():
            if key not in ['score', 'of_cdes']: # Exclude score (already printed) and long lists
                print(f"   {key.replace('_', ' ').title()}: {value}")

        if 'of_cdes' in metadata:
            cde_list = metadata['of_cdes']
            cde_count = len(cde_list)
            if cde_count > 0:
                cde_display = ", ".join(cde_list[:5]) + (f" ... (+{cde_count-5} more)" if cde_count > 5 else "")
                print(f"   Related CDEs: {cde_display}")
            else:
                print("   Related CDEs: None")

def get_search_choice():
    """Gets the user's choice of search type."""
    print("\nSI-Tamer Enhanced Semantic Search Tool")
    print_separator()
    print("Choose your search type:")
    print("1. PV Search         - Find CDEs from Permissible Value terms")
    print("2. NCIT Search       - Find CDEs from NCI Thesaurus concepts")
    print("3. CDE Definition    - Find CDEs by definition similarity")
    print("4. NCIT Definition   - Find NCIT concepts by definition similarity")
    print("5. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        print("Invalid choice. Please try again.")

def main():
    """Main interactive loop for the search tool."""
    print("Initializing SI-Tamer Enhanced Semantic Search...")
    
    searcher = None
    try:
        searcher = SemanticSearcher()
        print("Connected to database successfully!")
    except Exception as e:
        print(f"Failed to initialize searcher: {e}")
        print("Please check your environment variables in the .env file:")
        print("   - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        return
    
    try:
        while True:
            choice = get_search_choice()
            if choice == '5':
                break
            
            prompts = {
                '1': "Enter PV term (e.g., 'blood pressure'): ",
                '2': "Enter NCIT concept (e.g., 'hypertension'): ",
                '3': "Enter description for CDEs (e.g., 'patient age at diagnosis'): ",
                '4': "Enter description for NCIT concepts (e.g., 'cancer of the blood'): "
            }
            search_term = input(prompts[choice]).strip()
            if not search_term:
                print("Search term cannot be empty.")
                continue

            count_str = input("How many results? (default: 5): ").strip()
            result_count = int(count_str) if count_str.isdigit() else 5
            
            print("\nSearching...")
            
            results = []
            title = ""
            try:
                if choice == '1':
                    title = "PV Search Results"
                    results = searcher.find_cde_from_pv_term(search_term, top_k=result_count)
                elif choice == '2':
                    title = "NCIT Search Results"
                    results = searcher.find_cde_from_ncit_term(search_term, top_k=result_count)
                elif choice == '3':
                    title = "CDE Definition Search Results"
                    results = searcher.find_cde_by_definition_similarity(search_term, top_k=result_count)
                elif choice == '4':
                    title = "NCIT Definition Search Results"
                    results = searcher.find_ncit_by_definition_similarity(search_term, top_k=result_count)
                
                print_results(results, title, search_term)

            except Exception as e:
                print(f"Error during search: {e}")
                
            print("\n" + "-" * 80)
            continue_choice = input("Would you like to perform another search? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                break
                
    except KeyboardInterrupt:
        print("\n\nSearch interrupted.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if searcher:
            searcher.close()
        print("Goodbye!")

if __name__ == "__main__":
    main()