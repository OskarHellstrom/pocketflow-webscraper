from pocketflow import Flow
from nodes import (
    QueryInputNode,
    DecisionNode,
    DuckDuckGoSearchNode,
    GoogleSearchNode,
    WebCrawlNode,
    AnalyzerNode,
    HITLOutputNode,
    HumanFeedbackNode
)

def create_research_flow():
    """Create and return a web research flow based on the design document."""
    
    # Create nodes, adding retries for LLM-based nodes
    query_node = QueryInputNode()
    decision_node = DecisionNode(max_retries=3, wait=5)
    duckduckgo_node = DuckDuckGoSearchNode()
    google_node = GoogleSearchNode()
    crawl_node = WebCrawlNode()
    analyzer_node = AnalyzerNode(max_retries=3, wait=5)
    hitl_output_node = HITLOutputNode(max_retries=3, wait=5)
    feedback_node = HumanFeedbackNode()
    
    # Define the flow structure using action-based transitions:
    
    # 1. Start with the query
    query_node >> decision_node

    # 2. Decision node routes to the appropriate tool or HITL based on its returned action
    decision_node - "search_duckduckgo" >> duckduckgo_node
    decision_node - "search_google" >> google_node
    decision_node - "crawl_url" >> crawl_node
    decision_node - "send_to_hitl" >> hitl_output_node

    # 3. All tool nodes lead to the Analyzer node (using default transition)
    duckduckgo_node >> analyzer_node
    google_node >> analyzer_node
    crawl_node >> analyzer_node

    # 4. Analyzer node loops back to the Decision node (using default transition)
    analyzer_node >> decision_node

    # 5. HITL output leads to the Human Feedback node (using default transition)
    hitl_output_node >> feedback_node

    # 6. Human Feedback node loops back to the Decision node if more research is needed
    feedback_node - "continue_research" >> decision_node
    # If feedback_node returns anything else (e.g., "complete" or None/"default"), the flow ends.
    
    # Create flow starting with query node
    return Flow(start=query_node)

# Create the research flow
research_flow = create_research_flow()