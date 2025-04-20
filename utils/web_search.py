import os
import json
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from googleapiclient.discovery import build
from utils.debug import debug, debug_error

# Load environment variables
load_dotenv()

def search_duckduckgo(query, max_results=10):
    """
    Perform a web search using DuckDuckGo.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, link, and snippet
    """
    debug("DuckDuckGo", f"Searching for: {query} (max_results={max_results})")
    try:
        # Create DuckDuckGo search client
        ddgs = DDGS()
        
        # Perform search
        results = list(ddgs.text(query, max_results=max_results))
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": result.get("href", ""),
                "snippet": result.get("body", "")
            })
        
        debug("DuckDuckGo", f"Search returned {len(formatted_results)} results")
        return formatted_results
    
    except Exception as e:
        debug_error("DuckDuckGo", f"Error in search: {e}")
        print(f"Error in DuckDuckGo search: {e}")
        return [{
            "title": "Error performing search",
            "link": "",
            "snippet": f"An error occurred: {str(e)}"
        }]

def search_google(query, max_results=10):
    """
    Perform a web search using Google Custom Search API.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, link, and snippet
    """
    debug("Google", f"Searching for: {query} (max_results={max_results})")
    try:
        # Get API key and CSE ID from environment variables
        api_key = os.getenv("GOOGLE_API_KEY")
        cse_id = os.getenv("GOOGLE_CSE_ID")
        
        if not api_key or not cse_id:
            debug_error("Google", "Missing API credentials")
            raise ValueError("Missing Google API credentials. Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.")
        
        # Build Google Custom Search service
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Perform search
        debug("Google", "Sending search request", level=2)
        res = service.cse().list(q=query, cx=cse_id, num=max_results).execute()
        
        # Format results
        formatted_results = []
        for item in res.get('items', []):
            formatted_results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        debug("Google", f"Search returned {len(formatted_results)} results")
        return formatted_results
    
    except Exception as e:
        debug_error("Google", f"Error in search: {e}")
        print(f"Error in Google search: {e}")
        return [{
            "title": "Error performing search",
            "link": "",
            "snippet": f"An error occurred: {str(e)}"
        }]

# Simple test function
if __name__ == "__main__":
    test_query = "What is PocketFlow?"
    
    print("Testing DuckDuckGo search...")
    results = search_duckduckgo(test_query, max_results=3)
    print(json.dumps(results, indent=2))
    
    print("\nTesting Google search...")
    try:
        results = search_google(test_query, max_results=3)
        print(json.dumps(results, indent=2))
    except ValueError as e:
        print(f"Skipping Google search test: {e}") 