#!/usr/bin/env python3
"""
Testing script to compare baseline vs context-aware semantic search
for PV -> CDE mapping.
"""

import os
from dotenv import load_dotenv

from kg_toolkit.semantic_retrievers import SemanticSearcher

# Load environment variables from the .env file in the project root
load_dotenv()

def print_separator():
    """Prints a consistent separator line."""
    print("=" * 80)

def print_results(results, title):
    """Formats and prints the search results in a readable way."""
    print_separator()
    print(f"{title} (Total Results: {len(results)})")
    print_separator()

    if not results:
        print("No results found.\n")
        return

    for i, result in enumerate(results, 1):
        meta = result.get('metadata', {})
        score = meta.get('score', 0.0)
        combined_score = meta.get('combined_score')
        oc_term = meta.get('oc_term')

        print(f"\nResult {i}")
        print(f"  CDE: {meta.get('cde_term', 'N/A')} (Code: {meta.get('cde', 'N/A')})")
        print(f"  PV: {meta.get('pv_term', 'N/A')} (Code: {meta.get('pv_code', 'N/A')})")
        print(f"  Baseline Score: {score:.4f}")
        if combined_score is not None:
            print(f"  Combined Score (with OC): {combined_score:.4f}")
        if oc_term:
            print(f"  Object Class: {oc_term}")

        definition = result.get('text', '')
        if len(definition) > 100:
            definition = definition[:97] + "..."
        print(f"  Definition: {definition}")
    print()

def main():
    """Main function to run the interactive test session."""
    print("Initializing semantic searcher for context-aware testing...\n")
    searcher = None
    try:
        searcher = SemanticSearcher()

        while True:
            search_term = input("Enter PV term to test (or 'quit' to exit): ").strip()
            if search_term.lower() in ['quit', 'exit', 'q']:
                break

            top_k_str = input("Number of results to display (default 5): ").strip()
            top_k = int(top_k_str) if top_k_str.isdigit() else 5

            print("\nRunning baseline search...")
            baseline_results = searcher.find_cde_from_pv_term(search_term, top_k=top_k)
            print_results(baseline_results, "Baseline Search Results")

            print("\nRunning context-aware search (with OC re-ranking)...")
            context_results = searcher.contextaware_cde_from_pv(search_term, top_k=top_k)
            print_results(context_results, "Context-Aware Search Results")

            print("-" * 80)
            cont = input("Run another test? (y/n): ").strip().lower()
            if cont not in ['y', 'yes']:
                break

    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if searcher:
            searcher.close()
        print("Exiting test. Database connection closed.")

if __name__ == "__main__":
    main()