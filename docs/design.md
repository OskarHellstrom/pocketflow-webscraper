# PocketFlow Web Research Agent - Technical Design

## Overview

This document outlines the technical design for a dynamic web research agent built with PocketFlow. The system receives natural language queries, systematically gathers information from the web using various tools, synthesizes findings, assesses confidence, and presents reasoned answers to users with feedback capabilities.

## System Architecture

The architecture follows a node-based flow pattern where each node represents a specialized component with specific responsibilities in the research pipeline.

### Core Components

#### 1. Initial Query Node
- **Function**: Receives natural language queries from users
- **Implementation**: `QueryInputNode` class in `nodes.py`
- **Input**: User input (via console or API)
- **Output**: Raw query string
- **Shared Memory**: Stores the original query for reference throughout the process

#### 2. Decision Node
- **Function**: Central controller and reasoning engine for the research flow
- **Implementation**: `DecisionNode` class in `nodes.py`
- **Input**: 
  - Initial query (first execution)
  - Analyzer feedback (subsequent executions)
- **Responsibilities**:
  - Formulates search queries or identifies URLs
  - Selects appropriate tools (DuckDuckGo, Google, direct URL crawl)
  - Detects loops and handles blockages
  - Decides when to terminate research and present results
- **Output**: JSON object with next action instructions
  ```json
  {
    "next_action": "search_duckduckgo" | "search_google" | "crawl_url" | "send_to_hitl",
    "query_or_url": "<search query or URL>",
    "reasoning": "<explanation of decision>"
  }
  ```

#### 3. Tool Nodes
Three specialized nodes for web interaction:

##### 3.1 DuckDuckGo Search Node
- **Implementation**: `DuckDuckGoSearchNode` class in `nodes.py`
- **Input**: Search query from Decision Node
- **Function**: Performs web search using DuckDuckGo API
- **Output**: Raw search results (JSON)

##### 3.2 Google Search Node
- **Implementation**: `GoogleSearchNode` class in `nodes.py`
- **Input**: Search query from Decision Node
- **Function**: Performs web search using Google Search API
- **Output**: Raw search results (JSON)

##### 3.3 Web Crawl Node
- **Implementation**: `WebCrawlNode` class in `nodes.py`
- **Input**: URL from Decision Node
- **Function**: Performs HTTP requests and parses HTML content
- **Output**: Raw HTML content and extracted text

#### 4. Analyzer Node
- **Implementation**: `AnalyzerNode` class in `nodes.py`
- **Input**: Raw results from Tool Nodes
- **Responsibilities**:
  - Information extraction from raw data
  - Structuring and storing information in shared memory
  - Assessing relevance to the original query
  - Consistency checking with existing knowledge
  - Confidence scoring based on gathered information
  - Suggesting next research steps
- **Output**: JSON report to Decision Node
  ```json
  {
    "extracted_info": "<structured extracted data>",
    "assessment": "<summary of information relevance>",
    "confidence_score": 0.75,
    "suggestions_for_next_step": ["<suggested actions>"],
    "new_potential_urls": ["<URLs for potential crawling>"],
    "inconsistencies_found": "<any conflicting information>"
  }
  ```

#### 5. HITL Output Node
- **Implementation**: `HITLOutputNode` class in `nodes.py`
- **Input**: Final shared memory and analysis results
- **Function**: Synthesizes findings into human-readable format
- **Output**:
  - Direct answer to the original query
  - Research journey summary
  - Key sources list

#### 6. Human Feedback Node
- **Implementation**: `HumanFeedbackNode` class in `nodes.py`
- **Input**: Human response to HITL output
- **Function**: Processes feedback and determines if research should continue
- **Output**: Updated context for Decision Node or completion signal

### Shared Memory Structure
A persistent store for information throughout the research process:
```python
shared_memory = {
    "original_query": "<user's original question>",
    "iteration_count": 0,
    "research_history": [
        {"action": "search_google", "query": "...", "timestamp": "..."},
        # Additional history entries
    ],
    "extracted_information": {
        # Structured data from research process
    },
    "confidence_score": 0.0,
    "visited_urls": [],
    "final_answer": None
}
```

## Flow Design

The research flow follows this pattern:
1. Query Input → Decision Node (initial)
2. Decision Node → Tool Node (DuckDuckGo/Google/Crawl)
3. Tool Node → Analyzer Node
4. Analyzer Node → Decision Node (loop continues)
5. [When confidence threshold met or loop detected] → HITL Output
6. HITL Output → Human Feedback
7. [If feedback requires more research] → Decision Node (restart loop)

### Dynamic Routing Logic
The flow includes dynamic routing based on Decision Node output:
- `"next_action": "search_duckduckgo"` routes to DuckDuckGo Search Node
- `"next_action": "search_google"` routes to Google Search Node
- `"next_action": "crawl_url"` routes to Web Crawl Node
- `"next_action": "send_to_hitl"` routes to HITL Output Node

## Implementation Details

### LLM Integration
- The Decision and Analyzer nodes leverage Google Gemini LLM capabilities
- System prompts define behavior and processing logic
- Each node uses specialized prompts optimized for its function
- Using Gemini 2.5 Flash Preview model for efficient reasoning

### Web Tool Integration
- DuckDuckGo and Google Search nodes use appropriate APIs or libraries
- Web Crawl node uses requests and BeautifulSoup for HTML processing
- Rate limiting and error handling included for all web interactions

### Dependencies
- PocketFlow framework for node and flow management
- Google Generative AI API for LLM capabilities
- Web interaction libraries (requests, BeautifulSoup)
- Additional APIs for search functionality

## System Prompts

### Decision Node Prompt
```
You are the central Decision Node for a web research agent. Your role is to manage the research process, select appropriate tools, formulate search queries or identify URLs, and decide when the task is complete or requires human intervention.

Input Context:
- Initial Query: [The original user query]
- Current Analyzer Report: [Detailed report from Analyzer Node]
- Research History Summary: [Summary of recent actions and findings]
- Shared Memory Status: [Key entities and facts in knowledge base]

Task:
Based on the Input Context, determine the single best next action that moves toward answering the Initial Query efficiently while handling uncertainty and potential blockages.

Output Format:
JSON object with next_action, query_or_url, and reasoning fields.
```

### Analyzer Node Prompt
```
You are the Analyzer Node for a web research agent. Your task is to process raw data received from web tools, extract relevant information, structure it, assess its relevance, consistency, and trustworthiness, update shared memory, and provide a comprehensive report to the Decision Node.

Input Context:
- Initial Query: [The original user query]
- Raw Tool Output: [Raw output from the last executed Tool Node]
- Relevant Shared Memory: [Key information in shared memory]

Task:
Process the Raw Tool Output, extract relevant information, structure it, assess relevance, check consistency, evaluate trustworthiness, and formulate next steps.

Output Format:
JSON object with extracted_info, assessment, confidence_score, suggestions_for_next_step, new_potential_urls, and inconsistencies_found fields.
```

### HITL Output Prompt
```
You are the Report Generator for the Human-in-the-Loop interface. Your task is to synthesize research findings into a clear, concise answer, provide a brief research narrative, and list key supporting sources.

Input Context:
- Initial Query: [The original user query]
- Final Shared Memory Content: [Complete knowledge base content]
- Analyzer's Final Assessment: [Final assessment including confidence score]
- Research Journey Summary: [Log of main research steps]

Task:
Synthesize a clear answer to the Initial Query, create a concise research journey summary, and list key sources.

Output Format:
Human-readable report with Answer, Research Journey, and Key Sources sections.
```

## Extension Points

The system is designed for future enhancements:
1. Additional Tool Nodes for specialized data sources
2. Enhanced analysis capabilities in the Analyzer Node
3. More sophisticated loop detection and handling
4. Expanded user feedback mechanisms
5. Integration with additional LLMs or specialized models

## Implementation Roadmap

1. Core framework setup with PocketFlow
2. Basic node implementation with dummy functionality
3. Google Gemini LLM integration for Decision and Analyzer nodes
4. Tool node implementation with web APIs
5. Flow logic and routing implementation
6. Shared memory structure and management
7. Testing and refinement
8. User interface and feedback mechanisms
