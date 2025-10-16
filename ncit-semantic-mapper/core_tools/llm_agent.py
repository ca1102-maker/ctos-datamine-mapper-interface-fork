#!/usr/bin/env python3
"""
LangChain Agent for Neo4j Knowledge Graph Querying
Uses existing synonym finder and node matcher tools
"""
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_ollama import OllamaLLM 
from .config import Config
from langchain.output_parsers import PydanticOutputParser
from .core_tools.tools import (
    SemanticPVSearchTool,
    SemanticNCITSearchTool,
    SynonymFinderTool,
    SynonymByCodeTool,
    NodeMatcherTool,
    TermMatcherTool,
    ParallelSearchTool,
)

from pydantic import BaseModel
from typing import Optional, List, Literal
from json import dumps

class NCITMappingOutput(BaseModel):
    code: Optional[str]  # string OR null
    term: Optional[str]  # string OR null
    confidence: Literal["High", "Medium", "Low"]
    reasoning: str
    alternatives: List[str]


def create_fresh_agent():
    """Create and configure the LangChain agent"""
    
    Config.validate()
    
    llm = OllamaLLM(model="llama3.1-8") 
    
    # adding tools
    tools = [
        # Exact match tools (highest priority)
        TermMatcherTool(),
        NodeMatcherTool(),
        
        # Synonym tools (medium priority) 
        ParallelSearchTool(),
        SynonymFinderTool(),
        SynonymByCodeTool(),
        SemanticPVSearchTool(),
        SemanticNCITSearchTool()
    ]
    
    # creating fresh memory instance 
    fresh_memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # prompt engineering for the agent
    system_prompt = """
    You are an expert medical data mapper specializing in NCIT (National Cancer Institute Thesaurus) terminology.
    Your job is to help map raw medical data values to standardized NCIT terms and codes. 
    
    IMPORTANT: Focus ONLY on the current input. Do not reference previous queries or results.

    Available Tools (in order of preference):
    1. EXACT MATCH TOOLS (use first):
       - term_matcher: Find exact matches for term names
       - node_matcher: Find exact matches for NCIT codes
    
    2. PARALLEL SEARCH TOOL (use if exact match fails):
       - parallel_search: Executes synonym search and both semantic searches in parallel for maximum efficiency
       - This combines synonym_finder, semantic_pv_search, and semantic_ncit_search into one operation
    
    3. INDIVIDUAL TOOLS (fallback if needed):
       - synonym_finder: Find synonyms for permissible values 
       - synonym_by_code: Find synonyms using NCIT codes
       - semantic_pv_search: Find semantically similar terms through PV matching
       - semantic_ncit_search: Find semantically similar terms through NCIT concept matching
    
    Examples of proper tool usage:
    - For a term: term_matcher -> parallel_search (if exact match fails)
    - For a code that starts with C: node_matcher -> parallel_search (if exact match fails)
    - For a set of strings or phrase: term_matcher -> parallel_search (if exact match fails)
    
    The parallel_search tool will automatically run synonym and semantic searches simultaneously, providing comprehensive results in one operation.

    Always provide:
    - The recommended NCIT code and term (if found)
    - Confidence level (High/Medium/Low)
    - Reasoning for your recommendation (along with the sequence of steps you took, and the tools you used)
    - Alternative options if available

    You MUST:
    - Only use the database as your source of truth
    - Only use the provided tools
    - Focus ONLY on the current input
    
    You MUST NOT:
    - Make up answers when the database gives no results
    - Reference previous queries or results
    - Use action names that aren't actual tools
    
    Be thorough but concise in your analysis.
    
    Output requirements:
    - Respond ONLY with valid JSON
    - Do not include explanations, markdown, or backticks
    - JSON object must include exactly these keys:
      {
        "code": string | null,
        "term": string | null,
        "confidence": "High" | "Medium" | "Low",
        "reasoning": string,
        "alternatives": array
      }
    - If you cannot find a result, set code and term to null and explain in reasoning
    """
    
    # Initialize agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=7,
        memory = fresh_memory
    )
    
    return agent, system_prompt

def map_raw_data_isolated(agent, system_prompt, raw_value):
    """Map a raw data value to NCIT terminology"""

    prompt = f""" 

    {system_prompt}
    
    Raw medical data value to map: "{raw_value}"
    
    """
    parser = PydanticOutputParser(pydantic_object=NCITMappingOutput)
    #This will take the raw text from the LLM and parse it into the schema
    try:
        response = agent.run(prompt)
        # The below code will try to parse the response using the strict schema
        response = agent.run(prompt)
        parsed = parser.parse(response)
        return parsed.json()  # returns a JSON string
    except Exception:
        # Last resort returns valid JSON-like structure (dictionary) matching the schema is returned
        return NCITMappingOutput(
            code=None,
            term=None,
            confidence="Low",
            reasoning=str(response),
            alternatives=[]
        ).json()

def create_agent():
    """Legacy function for backward compatibility - DEPRECATED"""
    return create_fresh_agent()

def map_raw_data(agent, system_prompt, raw_value):
    """Legacy function for backward compatibility - DEPRECATED"""
    return map_raw_data_isolated(raw_value)