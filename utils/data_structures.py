from typing import TypedDict, List, Dict, Any, Optional

class Decision(TypedDict):
    next_action: str # e.g., "search_duckduckgo", "crawl_url", "send_to_hitl"
    query_or_url: Optional[str]
    reasoning: str

class ToolOutput(TypedDict):
    tool: str # e.g., "duckduckgo_search", "google_search", "web_crawl"
    query: Optional[str] # Query used for search tools
    url: Optional[str] # URL used for crawl tool
    results: Optional[List[Dict[str, Any]]] # Results from search tools
    content: Optional[Dict[str, Any]] # Results from crawl tool

class AnalyzerReport(TypedDict):
    extracted_info: Dict[str, Any]
    assessment: str
    confidence_score: float
    suggestions_for_next_step: List[str]
    new_potential_urls: List[str]
    inconsistencies_found: Optional[str] 