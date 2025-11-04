from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from pydantic import BaseModel, Field
from .synonym_tool import get_synonyms
from .exact_match import get_node_match
from .semantic_retrievers import SemanticSearcher
import asynchio

# Define input schemas
class QueryInput(BaseModel):
    query: str = Field(description="search term or code")

class SynonymFinderTool(BaseTool):
    name: str = "synonym_finder"
    description: str = """
    Useful for finding synonyms of a given permissible value (PV) term.
    Use this tool when the input is a permissible value like 'prostata' or 'M0'.
    Returns a list of synonyms for these permissible values from the knowledge graph, when an exact match cannot be found.
    """
    args_schema: type[BaseModel] = QueryInput

    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            synonym_finder = get_synonyms()
            synonyms = synonym_finder.get_synonyms_from_pv(query.strip())
            if synonyms:
                return f"Found {len(synonyms)} synonyms for '{query}': {', '.join(synonyms)}"
            else:
                return f"No synonyms found for '{query}'"
        except Exception as e:
            return f"Error searching for synonyms: {str(e)}"
    
    async def _arun(
        self, 
        query: str, 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return self._run(query, run_manager=run_manager.get_sync() if run_manager else None)

class SynonymByCodeTool(BaseTool):
    name: str = "synonym_by_code"
    description: str = """
    Useful for finding synonyms using an NCIT code (like C4890).
    Use this tool when the input is an NCIT code starting with 'C'.
    Returns synonyms associated with that specific code when an exact match for the code cannot be found in the database.
    """
    args_schema: type[BaseModel] = QueryInput
    
    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            synonym_finder = get_synonyms()
            code = query.strip().upper()
            synonyms = synonym_finder.get_synonyms_from_termcode(code)
            if synonyms:
                return f"Found {len(synonyms)} synonyms for code '{code}': {', '.join(synonyms)}"
            else:
                return f"No synonyms found for code '{code}'"
        except Exception as e:
            return f"Error searching for synonyms by code: {str(e)}"
    
    async def _arun(
        self, 
        query: str, 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return self._run(query, run_manager=run_manager.get_sync() if run_manager else None)

class NodeMatcherTool(BaseTool):
    name: str = "node_matcher"
    description: str = """
    Useful for finding exact node information by NCIT code. This tool is used to find the exact match in the database for the given code.
    Use this tool if the input is an NCIT code like 'C2357'.
    Returns detailed information about the node including term, definition, type.
    """
    args_schema: type[BaseModel] = QueryInput
    
    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            matcher = get_node_match()
            code = query.strip().upper()
            result = matcher.get_exact_match_from_code(code)
            if result:
                return f"Found node for '{code}': Term='{result['term']}', Type='{result['type']}', Definition='{result['definition'][:200]}...'"
            else:
                return f"No node found for code '{code}'"
        except Exception as e:
            return f"Error finding node: {str(e)}"
    
    async def _arun(
        self, 
        query: str, 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return self._run(query, run_manager=run_manager.get_sync() if run_manager else None)

class TermMatcherTool(BaseTool):
    name: str = "term_matcher"
    description: str = """
    Useful for finding exact node information by term name. This tool is used to find the exact match in the database for the given term name.
    Use this tool when the input is a term like 'Lung Carcinoma'.
    Returns detailed information including NCIT code, definition, type.
    """
    args_schema: type[BaseModel] = QueryInput
    
    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            matcher = get_node_match()
            term = query.strip()
            result = matcher.get_exact_match_from_term(term)
            if result:
                return f"Found node for '{term}': Code='{result['code']}', Type='{result['type']}', Definition='{result['definition'][:200]}...'"
            else:
                return f"No exact match found for term '{term}'"
        except Exception as e:
            return f"Error finding term: {str(e)}"
    
    async def _arun(
        self, 
        query: str, 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return self._run(query, run_manager=run_manager.get_sync() if run_manager else None)

class SemanticPVSearchTool(BaseTool):
    name: str = "semantic_pv_search"
    description: str = """
    Useful for finding semantically similar CDEs through permissible value matching.
    Use this tool when exact matches and synonyms fail, and you need to find related medical concepts.
    This performs vector-based semantic search on PV terms to find similar permissible values and their associated CDEs.
    Best for general medical terms like 'blood pressure', 'cancer staging', 'diabetes symptoms'.
    Returns similarity scores and related CDE information.
    """
    args_schema: type[BaseModel] = QueryInput
    
    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            searcher = SemanticSearcher()
            results = searcher.find_cde_from_pv_term(query.strip(), top_k=3)
            searcher.close()
            
            if not results:
                return f"No semantic matches found for PV term '{query}'"
            
            response_parts = [f"Found {len(results)} semantic matches for '{query}' through PV search:"]
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                score = metadata['score']
                pv_term = metadata['pv_term']
                pv_code = metadata['pv_code']
                cde_term = metadata['cde_term']
                cde_code = metadata['cde']
                
                response_parts.append(
                    f"\n{i}. PV: '{pv_term}' (Code: {pv_code}) -> CDE: '{cde_term}' (Code: {cde_code}) [Similarity: {score:.4f}]"
                )
            
            return "".join(response_parts)
            
        except Exception as e:
            return f"Error in semantic PV search: {str(e)}"
    
    async def _arun(
        self, 
        query: str, 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return self._run(query, run_manager=run_manager.get_sync() if run_manager else None)

class SemanticNCITSearchTool(BaseTool):
    name: str = "semantic_ncit_search"
    description: str = """
    Useful for finding semantically similar CDEs through NCIT term concept matching.
    Use this tool when exact matches and synonyms fail, and you need to find related standardized medical concepts.
    This performs vector-based semantic search on NCIT terms to find similar concepts and their associated PVs and CDEs.
    Best for standardized medical terminology like 'hypertension', 'neoplasm', 'anatomical structures'.
    Returns similarity scores and comprehensive relationship information.
    """
    args_schema: type[BaseModel] = QueryInput
    
    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            searcher = SemanticSearcher()
            results = searcher.find_cde_from_ncit_term(query.strip(), top_k=3)
            searcher.close()
            
            if not results:
                return f"No semantic matches found for NCIT term '{query}'"
            
            response_parts = [f"Found {len(results)} semantic matches for '{query}' through NCIT search:"]
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                score = metadata['score']
                concept_term = metadata['concept_term']
                concept_code = metadata['concept_code']
                pv_term = metadata['pv_term']
                pv_code = metadata['pv_code']
                cde_codes = metadata['of_cdes']
                
                cde_summary = f"{len(cde_codes)} CDEs" if cde_codes else "No CDEs"
                
                response_parts.append(
                    f"\n{i}. NCIT: '{concept_term}' (Code: {concept_code}) -> PV: '{pv_term}' (Code: {pv_code}) -> {cde_summary} [Similarity: {score:.4f}]"
                )
            
            return "".join(response_parts)
            
        except Exception as e:
            return f"Error in semantic NCIT search: {str(e)}"
    
    async def _arun(
        self, 
        query: str, 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return self._run(query, run_manager=run_manager.get_sync() if run_manager else None)


    # Async helper functions for parallel execution
async def _synonym_search_async(query: str) -> str:
    """Async wrapper for synonym search"""
    def _sync_synonym_search():
        try:
            synonym_finder = get_synonyms()
            synonyms = synonym_finder.get_synonyms_from_pv(query.strip())
            if synonyms:
                return f"Found {len(synonyms)} synonyms for '{query}': {', '.join(synonyms)}"
            else:
                return f"No synonyms found for '{query}'"
        except Exception as e:
            return f"Error searching for synonyms: {str(e)}"
    
    return await asyncio.to_thread(_sync_synonym_search)

async def _semantic_pv_search_async(query: str) -> str:
    """Async wrapper for semantic PV search"""
    def _sync_semantic_pv_search():
        try:
            searcher = SemanticSearcher()
            results = searcher.find_cde_from_pv_term(query.strip(), top_k=3)
            searcher.close()
            
            if not results:
                return f"No semantic matches found for PV term '{query}'"
            
            response_parts = [f"Found {len(results)} semantic matches for '{query}' through PV search:"]
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                score = metadata['score']
                pv_term = metadata['pv_term']
                pv_code = metadata['pv_code']
                cde_term = metadata['cde_term']
                cde_code = metadata['cde']
                
                response_parts.append(
                    f"\n{i}. PV: '{pv_term}' (Code: {pv_code}) -> CDE: '{cde_term}' (Code: {cde_code}) [Similarity: {score:.4f}]"
                )
            
            return "".join(response_parts)
            
        except Exception as e:
            return f"Error in semantic PV search: {str(e)}"
    
    return await asyncio.to_thread(_sync_semantic_pv_search)

async def _semantic_ncit_search_async(query: str) -> str:
    """Async wrapper for semantic NCIT search"""
    def _sync_semantic_ncit_search():
        try:
            searcher = SemanticSearcher()
            results = searcher.find_cde_from_ncit_term(query.strip(), top_k=3)
            searcher.close()
            
            if not results:
                return f"No semantic matches found for NCIT term '{query}'"
            
            response_parts = [f"Found {len(results)} semantic matches for '{query}' through NCIT search:"]
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                score = metadata['score']
                concept_term = metadata['concept_term']
                concept_code = metadata['concept_code']
                pv_term = metadata['pv_term']
                pv_code = metadata['pv_code']
                cde_codes = metadata['of_cdes']
                
                cde_summary = f"{len(cde_codes)} CDEs" if cde_codes else "No CDEs"
                
                response_parts.append(
                    f"\n{i}. NCIT: '{concept_term}' (Code: {concept_code}) -> PV: '{pv_term}' (Code: {pv_code}) -> {cde_summary} [Similarity: {score:.4f}]"
                )
            
            return "".join(response_parts)
            
        except Exception as e:
            return f"Error in semantic NCIT search: {str(e)}"
    
    return await asyncio.to_thread(_sync_semantic_ncit_search)

    #_synonym_search_async() → async synonym search
    #_semantic_pv_search_async() → async permissible value search
    #_semantic_ncit_search_async() → async NCIT search
    #However, these asynch functions run independently. The ParallelSearchTool below 
    #runs all three at the same time, collects all results, and returns them together

    #
    class ParallelSearchTool(BaseTool):
        name: str = "parallel_search"
        description: str = """
        Use this tool after exact match tools fail. Executes synonym search and both semantic searches (PV and NCIT) in parallel for maximum efficiency.
        This tool combines the functionality of synonym_finder, semantic_pv_search, and semantic_ncit_search into a single parallel operation.
        Returns comprehensive results from all three search methods simultaneously.
        """
        args_schema: type[BaseModel] = QueryInput

        def _run(
            self, 
            query: str, 
            run_manager: Optional[CallbackManagerForToolRun] = None
        ) -> str:
            """Synchronous version that runs the async version"""
            try:
                # Run the async version in a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self._arun(query, run_manager))
                    return result
                finally:
                    loop.close()
            except Exception as e:
                return f"Error in parallel search: {str(e)}"
    
        async def _arun(
            self, 
            query: str, 
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None
        ) -> str:
            """Execute synonym and semantic searches in parallel"""
            try:
                # Create tasks for all three searches
                tasks = [
                    asyncio.create_task(_synonym_search_async(query)),
                    asyncio.create_task(_semantic_pv_search_async(query)),
                    asyncio.create_task(_semantic_ncit_search_async(query))
                ]
                #Each of those async functions runs concurrently in its own thread using asyncio.to_thread.
            
                # Wait for all tasks to complete concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
                # Format the combined results
                response_parts = [f"PARALLEL SEARCH RESULTS for '{query}':\n"]
                response_parts.append("=" * 50)
            
                # Process each result
                search_types = ["SYNONYM SEARCH", "SEMANTIC PV SEARCH", "SEMANTIC NCIT SEARCH"]
            
                for i, (search_type, result) in enumerate(zip(search_types, results)):
                    response_parts.append(f"\n{search_type}:")
                    response_parts.append("-" * 30)
                
                    if isinstance(result, Exception):
                        response_parts.append(f"Error: {str(result)}")
                    else:
                        response_parts.append(result)
                
                return "".join(response_parts)
        #Output will hopefully look like this: 
        """ PARALLEL SEARCH RESULTS for 'cancer':
            ==================================================

            SYNONYM SEARCH:
            ------------------------------
            Found synonyms: carcinoma, malignancy, tumor

            SEMANTIC PV SEARCH:
            ------------------------------
            Found 2 PV matches with high similarity scores.

            SEMANTIC NCIT SEARCH:
            ------------------------------
            Found 1 NCIT match: Code C1234 (term: 'Carcinoma').

            """
            
            except Exception as e:
                return f"Error in parallel search execution: {str(e)}"

    #Below is an example of using the Parallel Search Tool
    #You call ParallelSearchTool._run("diabetes").
    #It starts an event loop and calls _arun().
    #_arun() launches three tasks concurrently:
    # 1. _synonym_search_async()
    # 2. _semantic_pv_search_async()
    # 3. _semantic_ncit_search_async()
    #All three execute simultaneously, each in its own thread, via asyncio.to_thread().
    #The function waits (await asyncio.gather()) for all results.
    #Once it all returns, it formats and prints a unified report.







