#!/usr/bin/env python3
"""
Test script for the synonym finder.
Allows a user to interactively choose between searching by PV term or NCIT code.
"""
import sys
import os
from dotenv import load_dotenv

from kg_toolkit.synonym_tool import get_synonyms  

# Load environment variables from the .env file in the project root
load_dotenv()

def get_search_type():
    """Gets the user's choice for the search type."""
    while True:
        print("\nChoose search method:")
        print("1. Search by Permissible Value (PV) - e.g., 'prostate'")
        print("2. Search by NCIT Code - e.g., 'C4878'")
        print("3. Quit")
        
        choice = input("\nEnter your choice (1, 2, or 3): ").strip()
        
        if choice == '1':
            return 'pv'
        elif choice == '2':
            return 'code'
        elif choice == '3':
            return 'quit'
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def search_by_pv(synonym_finder):
    """Handles the workflow for searching by PV term."""
    pv_term = input("Enter a permissible value to search for: ").strip()
    if not pv_term:
        print("Please enter a valid permissible value.")
        return
    
    print()
    synonyms = synonym_finder.get_synonyms_from_pv(pv_term)
    if not synonyms:
        print(f"-> No synonyms found for PV '{pv_term}'")

def search_by_code(synonym_finder):
    """Handles the workflow for searching by NCIT code."""
    code = input("Enter an NCIT code to search for (e.g., C4878): ").strip().upper()
    if not code:
        print("Please enter a valid NCIT code.")
        return
    
    print()
    synonyms = synonym_finder.get_synonyms_from_termcode(code)
    if not synonyms:
        print(f"-> No synonyms found for NCIT code '{code}'")

def main():
    """Main function to run the interactive test."""
    
    NEO4J_URI = os.getenv("NEO4J_URI")  
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")             
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")          
    
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("Error: Missing Neo4j credentials. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file.")
        sys.exit(1)

    print("=== Cancer Knowledge Graph Synonym Finder Test ===")
    
    synonym_finder = None
    try:
        print("\nConnecting to Neo4j database...")
        synonym_finder = get_synonyms(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        print("Connection successful!")
        
        while True:
            print("\n" + "-" * 60)
            search_type = get_search_type()
            
            if search_type == 'quit':
                break
            elif search_type == 'pv':
                search_by_pv(synonym_finder)
            elif search_type == 'code':
                search_by_code(synonym_finder)
            
            continue_choice = input("\nWould you like to perform another search? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                break
            
    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")
    finally:
        if synonym_finder and hasattr(synonym_finder, 'close'):
            synonym_finder.close()
        print("\nThanks for testing!")

if __name__ == "__main__":
    main()