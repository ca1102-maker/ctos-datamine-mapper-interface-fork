#!/usr/bin/env python3
"""
Interactive Test Script for the LLM Agent.

This script initializes the agent and allows you to input medical terms manually
to see how the agent maps them to NCIT codes using the configured tools.
"""

import os
import sys
import time
from dotenv import load_dotenv

try:
    from kg_toolkit.llm_agent_4o import create_fresh_agent, map_raw_data_isolated
except ImportError:
    from kg_toolkit.utils.llm_agent_4o import create_fresh_agent, map_raw_data_isolated

try:
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
except Exception as e:
    print(f"Warning: Could not load .env file. Error: {e}")

def print_separator():
    print("-" * 60)

def main():
    print("=== Interactive LLM Agent Test ===")
    
    # 1. Check Credentials
    if not os.getenv("NEO4J_URI"):
        print("ERROR: NEO4J_URI not found in environment variables.")
        print("Please ensure your .env file is set up correctly.")
        return

    agent_executor = None
    system_prompt = None

    # 2. Initialize Agent
    print("\nInitializing Agent (Connecting to Neo4j and Ollama)...")
    try:
        start_time = time.time()
        agent_executor, system_prompt = create_fresh_agent()
        elapsed = time.time() - start_time
        print(f"✅ Agent initialized successfully in {elapsed:.2f} seconds.")
        print(f"   Loaded {len(agent_executor.tools)} tools.")
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {e}")
        print("Please ensure Neo4j and Ollama are running.")
        return

    # 3. Interaction Loop
    while True:
        print_separator()
        print("Enter a medical term to map (or 'q' to quit).")
        print("Examples: 'Lung Carcinoma', 'Prostate', 'Supercalifragilistic'")
        
        user_input = input("\nQuery > ").strip()
        
        if user_input.lower() in ['q', 'quit', 'exit']:
            break
        
        if not user_input:
            continue

        print(f"\n🤖 Agent is thinking about '{user_input}'...")
        
        try:
            # Run the agent
            start_time = time.time()
            result = map_raw_data_isolated(agent_executor, system_prompt, user_input)
            elapsed = time.time() - start_time
            
            print(f"\n⏱️  Response generated in {elapsed:.2f} seconds.")
            print("📝 Agent Output:")
            print("=" * 40)
            print(result)
            print("=" * 40)

        except Exception as e:
            print(f"\n❌ Error during execution: {e}")

    print("\nGoodbye!")

if __name__ == "__main__":
    main()