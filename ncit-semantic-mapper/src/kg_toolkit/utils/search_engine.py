import re
from datetime import datetime

from kg_toolkit.llm_agent_4o import map_raw_data_isolated

class SearchEngine:
    """
    A wrapper around the LangChain agent to provide a consistent interface
    for the Streamlit application.
    """
    
    def __init__(self, agent_executor=None, system_prompt=None):
        """
        Initializes the SearchEngine with a pre-configured agent and system prompt.
        
        Args:
            agent_executor: The initialized LangChain agent executor.
            system_prompt (str): The system prompt used to configure the agent.
        """
        self.agent_executor = agent_executor
        self.system_prompt = system_prompt
    
    def search(self, query: str) -> dict:
        """
        Performs a search using the configured agent and returns a structured dictionary.
        
        Args:
            query (str): The user's search query.
            
        Returns:
            A dictionary containing the raw response, query, timestamp, and parsed data.
        """
        if not self.agent_executor or not self.system_prompt:
            raise ValueError("SearchEngine is not initialized. Please provide an agent_executor and system_prompt.")
        
        # Call the core agent function from the llm_agent_4o module
        raw_result = map_raw_data_isolated(
            self.agent_executor,
            self.system_prompt,
            query
        )
        
        # Structure the final output
        return {
            'raw_response': raw_result,
            'query': query,
            'timestamp': datetime.now(),
            'parsed_data': self.parse_response(raw_result)
        }
    
    def parse_response(self, response: str) -> dict:
        """
        A simple parser to extract key information from the agent's raw text response.
        
        Args:
            response (str): The raw string output from the agent's run.
            
        Returns:
            A dictionary with extracted fields like final answer, NCIT code, and confidence.
        """
        parsed = {
            'final_answer': None,
            'ncit_code': None,
            'ncit_term': None,
            'confidence': None,
            'tool_results': {} # Placeholder for more advanced parsing
        }
        
        # Extract the final answer section
        if "Final Answer:" in response:
            parsed['final_answer'] = response.split("Final Answer:")[-1].strip()
        
        # Use regex to find potential NCIT code patterns (e.g., C12345)
        code_match = re.search(r'([A-Z]\d+)', response)
        if code_match:
            parsed['ncit_code'] = code_match.group(1)
        
        # Use regex to find the confidence level, ignoring case
        conf_match = re.search(r'Confidence[:\s]*(High|Medium|Low)', response, re.IGNORECASE)
        if conf_match:
            parsed['confidence'] = conf_match.group(1).capitalize()
        
        return parsed