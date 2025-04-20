from pocketflow import Node
import json
import time
from typing import Dict, Any, Optional
from utils.call_llm import call_llm
from utils.web_search import search_duckduckgo, search_google
from utils.web_crawl import crawl_url
from utils.debug import debug, debug_error, DEBUG_LEVEL
from utils.data_structures import Decision, ToolOutput, AnalyzerReport

class QueryInputNode(Node):
    """Node for receiving the initial query from the user."""
    
    def exec(self, _):
        debug("QueryInputNode", "Starting execution")
        try:
            # Get question directly from user input
            user_question = input("Enter your research query: ")
            debug("QueryInputNode", f"Received query: {user_question}")
            return user_question
        except Exception as e:
            debug_error("QueryInputNode", e)
            raise
    
    def post(self, shared, prep_res, exec_res):
        # Store the user's question and initialize shared memory
        shared["original_query"] = exec_res
        shared["iteration_count"] = 0
        shared["research_history"] = []
        shared["extracted_information"] = {}
        shared["confidence_score"] = 0.0
        shared["visited_urls"] = []
        shared["final_answer"] = None
        
        # Route to the next node
        return "default"

class DecisionNode(Node):
    """Central controller node that decides the next research action."""
    
    def prep(self, shared):
        # Prepare input for the decision-making process
        context = {
            "initial_query": shared["original_query"],
            "iteration_count": shared["iteration_count"]
        }
        
        # Add analyzer report if available
        if "analyzer_report" in shared:
            context["analyzer_report"] = shared["analyzer_report"]
        
        # Add research history
        context["research_history"] = shared["research_history"]
        
        return context
    
    def exec(self, context):
        debug("DecisionNode", f"Starting execution (iteration: {context['iteration_count']})")
        try:
            # Construct prompt for the LLM
            prompt = f"""You are the central Decision Node for a web research agent. Your role is to manage the research process, select appropriate tools, formulate search queries or identify URLs, and decide when the task is complete or requires human intervention.

Input Context:
- Initial Query: {context['initial_query']}
- Current Iteration: {context['iteration_count']}
"""

            # Add analyzer report if available
            if "analyzer_report" in context:
                prompt += f"- Current Analyzer Report: {json.dumps(context['analyzer_report'])}\n"
            
            # Add research history summary
            if context["research_history"]:
                history_summary = "\n".join([f"- {i+1}. {entry['action']}: {entry['query_or_url']}" 
                                           for i, entry in enumerate(context["research_history"][-3:])])
                prompt += f"\nRecent Research History:\n{history_summary}\n"
            
            prompt += """
Task:
Based on the Input Context, determine the single best next action. Your decision should move towards answering the Initial Query efficiently while handling uncertainty and potential blockages.

Output Format:
Respond ONLY with a JSON object containing the decided next action and its parameters. Do not include any explanatory text before or after the JSON.

Example Output:
```json
{
  "next_action": "search_duckduckgo",
  "query_or_url": "latest AI research trends",
  "reasoning": "Initial query is broad, starting with a web search to gather general information."
}
```

Now, provide the JSON object for the current task:
"""
            
            # Call LLM to get the decision
            debug("DecisionNode", f"Calling LLM for decision with query: {context['initial_query']}")
            response = call_llm(prompt)
            
            # Log the raw response for debugging
            debug("DecisionNode", f"Raw LLM response: {response[:100]}...", level=3)
            
            # Try to extract JSON from the response if it's not pure JSON
            try:
                # Check if response is wrapped in backticks or other markers
                if "```json" in response:
                    # Extract JSON from code block
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    if json_end > json_start:
                        json_str = response[json_start:json_end].strip()
                        debug("DecisionNode", "Found JSON in code block", level=2)
                    else:
                        json_str = response
                elif "```" in response:
                    # Extract from generic code block
                    json_start = response.find("```") + 3
                    json_end = response.find("```", json_start)
                    if json_end > json_start:
                        json_str = response[json_start:json_end].strip()
                        debug("DecisionNode", "Found JSON in code block", level=2)
                    else:
                        json_str = response
                elif "{" in response and "}" in response:
                    # Try to extract JSON object
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    if json_end > json_start:
                        json_str = response[json_start:json_end].strip()
                        debug("DecisionNode", "Extracted JSON object from text", level=2)
                    else:
                        json_str = response
                else:
                    json_str = response
                
                debug("DecisionNode", f"Attempting to parse: {json_str[:100]}...", level=3)
                decision = json.loads(json_str)
                
                # Validate the decision
                if "next_action" not in decision or "query_or_url" not in decision or "reasoning" not in decision:
                    debug_error("DecisionNode", "Decision is missing required fields")
                    raise ValueError("Decision is missing required fields")
                
                debug("DecisionNode", f"Next action: {decision['next_action']}")
                return decision
                
            except json.JSONDecodeError as e:
                debug_error("DecisionNode", f"Failed to parse JSON response: {e}")
                # Fallback for invalid JSON - construct a reasonable default
                debug("DecisionNode", "Using fallback decision - perform DuckDuckGo search")
                return {
                    "next_action": "search_duckduckgo",
                    "query_or_url": context['initial_query'],
                    "reasoning": "Failed to parse decision response, falling back to direct search"
                }
        except Exception as e:
            debug_error("DecisionNode", e)
            raise
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Decision):
        # Increment iteration count
        shared["iteration_count"] += 1
        
        # Add to research history
        shared["research_history"].append({
            "action": exec_res["next_action"],
            "query_or_url": exec_res["query_or_url"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reasoning": exec_res["reasoning"]
        })
        
        # Store the decision details for potential use by other nodes
        shared["current_decision"] = exec_res 
        # Store the reasoning for the AnalyzerNode (Improvement 5)
        shared["last_decision_reasoning"] = exec_res["reasoning"]
        
        # Get the action to return
        action = exec_res["next_action"]
        
        # === Structured Log (if DEBUG_LEVEL=0) ===
        if DEBUG_LEVEL == 0:
            print("\n" + "="*20 + f" Iteration {shared['iteration_count']} " + "="*20)
            print("DECISION:")
            print(f"  Reasoning: {exec_res['reasoning']}")
            print(f"  Action: {action}")
            if exec_res.get('query_or_url'):
                 print(f"  Target: {exec_res['query_or_url']}")
        # ============================================
        
        debug("DecisionNode", f"[OUTPUT] Storing current_decision, last_decision_reasoning. Returning action: {action}", level=2)
        return action

class DuckDuckGoSearchNode(Node):
    """Node for performing DuckDuckGo searches."""
    
    def prep(self, shared):
        # Get the query from the decision made in the previous step
        query = shared.get("current_decision", {}).get("query_or_url")
        debug("DuckDuckGoSearchNode", f"[INPUT] Received query: {query[:50] if query else 'None'}...", level=2)
        if not query:
             debug_error("DuckDuckGoSearchNode", "Missing query/url in current_decision")
             return None 
        return query
    
    def exec(self, query):
        # If prep failed to provide a query, skip execution
        if query is None:
             debug("DuckDuckGoSearchNode", "Skipping execution due to missing query in prep")
             return None

        debug("DuckDuckGoSearchNode", f"Searching DuckDuckGo for: {query}")
        try:
            # Perform DuckDuckGo search
            results = search_duckduckgo(query)
            debug("DuckDuckGoSearchNode", f"Got {len(results)} results")
            return results # Return results on success
        except Exception as e:
            error_message = f"Error during DuckDuckGo search: {e}"
            debug_error("DuckDuckGoSearchNode", error_message)
            # Return an error dictionary on failure
            return {"error": error_message}
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Any):
        # Skip post-processing if execution was skipped in prep
        # exec_res will be None if prep returned None
        if exec_res is None:
            debug("DuckDuckGoSearchNode", "[OUTPUT] Skipped storing output (prep failed).", level=2)
            return "default" 
        
        error = exec_res.get("error") if isinstance(exec_res, dict) else None
        results_data = exec_res if not error else None # Store results only if no error
        num_results = len(results_data) if results_data else 0
            
        # Store the tool output, including error if present
        tool_output: ToolOutput = {
            "tool": "duckduckgo_search",
            "query": prep_res,
            "results": results_data, 
            "url": None, 
            "content": None,
            "error": error # Add the error field
        }
        shared["latest_tool_output"] = tool_output
        
        if error:
            debug("DuckDuckGoSearchNode", f"[OUTPUT] Stored latest_tool_output with ERROR: {error}.", level=2)
        else:
            debug("DuckDuckGoSearchNode", f"[OUTPUT] Stored latest_tool_output (tool: {tool_output['tool']}, num_results: {num_results}).", level=2)
        
        # Always route to AnalyzerNode, even if there was an error
        return "default"

class GoogleSearchNode(Node):
    """Node for performing Google searches."""
    
    def prep(self, shared):
        # Get the query from the decision made in the previous step
        query = shared.get("current_decision", {}).get("query_or_url")
        if not query:
            debug_error("GoogleSearchNode", "Missing query/url in current_decision")
            return None
        return query
    
    def exec(self, query):
        # Skip if prep returned None
        if query is None:
            debug("GoogleSearchNode", "Skipping execution due to missing query in prep")
            return None
        
        debug("GoogleSearchNode", f"Searching Google for: {query}")
        try:    
            # Perform Google search
            results = search_google(query)
            debug("GoogleSearchNode", f"Got {len(results)} results")
            return results
        except Exception as e:
            debug_error("GoogleSearchNode", e)
            raise
    
    def post(self, shared, prep_res, exec_res):
        # Skip post-processing if execution was skipped
        if exec_res is None:
            return "default" # Still return default to proceed in the flow (to Analyzer)
            
        # Store the search results
        shared["latest_tool_output"] = {
            "tool": "google_search",
            "query": prep_res,
            "results": exec_res
        }
        
        # Route to the next node (AnalyzerNode)
        return "default"

class WebCrawlNode(Node):
    """Node for crawling specific URLs."""
    
    def prep(self, shared):
        # Get the URL from the decision made in the previous step
        url = shared.get("current_decision", {}).get("query_or_url")
        if not url:
            debug_error("WebCrawlNode", "Missing query/url in current_decision")
            return None 
        
        # Add to visited URLs
        if url not in shared["visited_urls"]:
            shared["visited_urls"].append(url)
            
        return url
    
    def exec(self, url):
        # Skip if prep failed to provide a URL
        if url is None:
            debug("WebCrawlNode", "Skipping execution due to missing URL in prep")
            return None
        
        debug("WebCrawlNode", f"Crawling URL: {url}")
        try:
            # Crawl the URL
            content = crawl_url(url)
            if content:
                content_length = len(content.get('content', ''))
                debug("WebCrawlNode", f"Fetched content ({content_length} chars)")
            else:
                debug_error("WebCrawlNode", "Failed to fetch content")
            return content
        except Exception as e:
            debug_error("WebCrawlNode", e)
            raise
    
    def post(self, shared, prep_res, exec_res):
        # Skip post-processing if execution was skipped
        if exec_res is None:
            return "default" # Still return default to proceed in the flow (to Analyzer)
            
        # Store the crawl results
        shared["latest_tool_output"] = {
            "tool": "web_crawl",
            "url": prep_res,
            "content": exec_res
        }
        
        # Route to the next node (AnalyzerNode)
        return "default"

class AnalyzerNode(Node):
    """Node for analyzing and synthesizing information from web sources."""
    
    def prep(self, shared: Dict[str, Any]):
        # Get the last decision made
        last_decision: Optional[Decision] = shared.get("current_decision")
        decision_was_hitl = last_decision and last_decision.get("next_action") == "send_to_hitl"
        tool_output: Optional[ToolOutput] = shared.get("latest_tool_output")

        # Log input status
        debug("AnalyzerNode", f"[INPUT] Checking conditions - Has tool output: {tool_output is not None}. Decision was HITL: {decision_was_hitl}", level=2)

        # Skip analysis if conditions met (no tool output or decision was HITL)
        if tool_output is None or decision_was_hitl:
            debug("AnalyzerNode", f"Skipping execution.")
            return None
        
        # Check if the tool output contains an error
        tool_error = tool_output.get("error")
        
        # Log details of the tool output being processed (including error)
        tool_name = tool_output.get("tool", "Unknown Tool")
        if tool_error:
             debug("AnalyzerNode", f"[INPUT] Preparing to analyze ERROR from {tool_name}: {tool_error[:100]}...", level=2)
        elif tool_name in ["duckduckgo_search", "google_search"]:
            query = tool_output.get("query", "N/A")
            num_results = len(tool_output.get("results", []))
            debug("AnalyzerNode", f"[INPUT] Preparing to analyze {tool_name} results for query: '{query[:50]}...' ({num_results} results received).", level=2)
        elif tool_name == "web_crawl":
            url = tool_output.get("url", "N/A")
            content_len = len(tool_output.get("content", {}).get("content", ""))
            debug("AnalyzerNode", f"[INPUT] Preparing to analyze {tool_name} content from URL: {url} ({content_len} chars received).", level=2)
        else:
             debug("AnalyzerNode", f"[INPUT] Preparing to analyze output from {tool_name}", level=2)
            
        # Prepare context for exec method, including the error if present
        context = {
            "initial_query": shared["original_query"],
            "latest_tool_output": tool_output, # Contains results OR error
            "extracted_information": shared["extracted_information"],
            "last_decision_reasoning": shared.get("last_decision_reasoning", "N/A")
        }
        return context
    
    def exec(self, context: Optional[Dict[str, Any]]):
        # Skip if prep returned None
        if context is None:
            # debug("AnalyzerNode", "Skipping execution (no tool output or going to HITL)") # Already logged in prep
            return None
        
        debug("AnalyzerNode", f"Analyzing data from tool: {context['latest_tool_output']['tool']}")
        try:
            # Construct prompt for the LLM
            prompt = f"""You are the Analyzer Node for a web research agent. Your task is to process raw data received from web tools, extract relevant information, structure it, assess its relevance, consistency, and trustworthiness, update the shared memory, and provide a comprehensive report and suggestions to the Decision Node.

Input Context:
- Initial Query: {context['initial_query']}
- Reasoning for last action: {context['last_decision_reasoning']} # Added Reasoning (Improvement 5)
- Tool Used: {context['latest_tool_output']['tool']}
"""

            # Add tool-specific context OR error message
            tool_error = context['latest_tool_output'].get('error')
            if tool_error:
                 prompt += f"- Tool Execution Error: {tool_error}\n"
            elif context['latest_tool_output']['tool'] in ['duckduckgo_search', 'google_search']:
                prompt += f"- Search Query: {context['latest_tool_output']['query']}\n"
                prompt += f"- Search Results: {json.dumps(context['latest_tool_output']['results'])}\n"
            elif context['latest_tool_output']['tool'] == 'web_crawl':
                prompt += f"- Crawled URL: {context['latest_tool_output']['url']}\n"
                # Limit content size to avoid token limits
                content_preview = "" # Default empty string
                crawl_content = context['latest_tool_output'].get('content')
                if crawl_content and isinstance(crawl_content, dict):
                     page_content = crawl_content.get('content', '')
                     content_preview = page_content[:5000] + "..." if len(page_content) > 5000 else page_content
                prompt += f"- Page Content: {content_preview}\n"
            
            if context['extracted_information']:
                prompt += f"\nExisting Information:\n{json.dumps(context['extracted_information'])}\n"
            
            prompt += """
Task:
1. Process the input. If a 'Tool Execution Error' is present, note the failure. Otherwise, process the raw tool output, considering the reasoning for why this tool was chosen.
2. Extract all information potentially relevant to the Initial Query or any of its identifiable parts. If there was a tool error, this might be empty.
3. Structure the extracted information clearly.
4. Assess the relevance of the extracted information (or the lack thereof due to error) to the Initial Query.
5. Compare with existing information, identify any inconsistencies.
6. Evaluate the trustworthiness of the sources (or note the tool failure).
7. Calculate a confidence score (likely low if there was a tool error or no relevant info found).
8. Suggest next logical research steps (e.g., trying a different tool if one failed, refining the query, or concluding if enough info is gathered or blocked).

Output Format:
Respond ONLY with a JSON object. Do not include any explanatory text before or after the JSON.

Example Output:
```json
{
  "extracted_info": {"main_topic": "AI Safety", "key_points": ["Alignment problem", "Potential risks"]},
  "assessment": "The search results provide a good overview of AI safety concerns.",
  "confidence_score": 0.8,
  "suggestions_for_next_step": ["Crawl specific paper URL found in results", "Search for counter-arguments"],
  "new_potential_urls": ["https://arxiv.org/abs/xxxx.xxxxx"],
  "inconsistencies_found": null
}
```

Now, provide the JSON object for the current task:
"""
            
            # Call LLM to analyze the data
            response = call_llm(prompt)
            
            # Log the raw response for debugging
            debug("AnalyzerNode", f"Raw LLM response: {response[:100]}...", level=3)
            
            # Try to extract JSON from the response if it's not pure JSON
            try:
                # Check if response is wrapped in backticks or other markers
                if "```json" in response:
                    # Extract JSON from code block
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip() if json_end > json_start else response
                elif "```" in response:
                    # Extract from generic code block
                    json_start = response.find("```") + 3
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip() if json_end > json_start else response
                elif "{" in response and "}" in response:
                    # Try to extract JSON object
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    json_str = response[json_start:json_end].strip() if json_end > json_start else response
                else:
                    json_str = response
                
                debug("AnalyzerNode", f"Attempting to parse: {json_str[:100]}...", level=3)
                analysis = json.loads(json_str)
                
                # Validate the analysis
                if "extracted_info" not in analysis or "confidence_score" not in analysis:
                    debug_error("AnalyzerNode", "Analysis is missing required fields")
                    raise ValueError("Analysis is missing required fields")
                
                debug("AnalyzerNode", f"Analysis complete with confidence: {analysis['confidence_score']}")
                return analysis
                
            except json.JSONDecodeError as e:
                debug_error("AnalyzerNode", f"Failed to parse JSON response: {e}")
                # Fallback for invalid JSON
                return {
                    "extracted_info": {},
                    "assessment": "Failed to parse analyzer response",
                    "confidence_score": 0.0,
                    "suggestions_for_next_step": ["Retry with different approach"],
                    "new_potential_urls": [],
                    "inconsistencies_found": None
                }
        except Exception as e:
            debug_error("AnalyzerNode", e)
            raise
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Optional[AnalyzerReport]):
        # Skip if exec returned None
        if exec_res is None:
            debug("AnalyzerNode", "[OUTPUT] Skipped storing output.", level=2)
            return "default"
            
        # Update shared memory with extracted information
        updated_keys = []
        if isinstance(exec_res["extracted_info"], dict):
            for key, value in exec_res["extracted_info"].items():
                shared["extracted_information"][key] = value
                updated_keys.append(key)
        
        shared["confidence_score"] = exec_res["confidence_score"]
        shared["analyzer_report"] = exec_res
        
        # === Structured Log (if DEBUG_LEVEL=0) ===
        if DEBUG_LEVEL == 0:
            tool_name = shared.get("latest_tool_output", {}).get("tool", "Unknown")
            print(f"\nANALYSIS (Input from {tool_name}):")
            print(f"  Assessment: {exec_res['assessment']}")
            print(f"  Confidence: {exec_res['confidence_score']:.2f}")
            # Optionally print suggestions if they exist and are not empty
            if exec_res.get('suggestions_for_next_step'):
                 print(f"  Suggestions: {exec_res['suggestions_for_next_step']}")
        # ============================================

        debug("AnalyzerNode", f"[OUTPUT] Stored analyzer_report. Confidence: {shared['confidence_score']}. Updated info keys: {updated_keys}", level=2)
        return "default"

class HITLOutputNode(Node):
    """Node for synthesizing findings and presenting them to the user."""
    
    def prep(self, shared):
        # This node runs when DecisionNode directs to 'send_to_hitl'.
        # We prepare the context needed for the final synthesis.
        context = {
            "initial_query": shared.get("original_query", "N/A"),
            "research_history": shared.get("research_history", []),
            "extracted_information": shared.get("extracted_information", {}),
            "final_analyzer_report": shared.get("analyzer_report", {})
        }
        return context
    
    def exec(self, context):
        # If prep returned None (although it shouldn't in this revised logic), skip.
        if context is None:
             debug("HITLOutputNode", "Skipping execution due to missing context in prep")
             return None

        debug("HITLOutputNode", "Synthesizing final answer")
        try:
            # Construct prompt for the LLM to synthesize the final answer
            prompt = f"""You are the Report Generator for the Human-in-the-Loop interface. Your task is to synthesize research findings into a clear, concise answer, provide a brief research narrative, and list key supporting sources.

Input Context:
- Initial Query: {context['initial_query']}
- Final Extracted Information: {json.dumps(context['extracted_information'])}
- Final Analyzer Assessment: {json.dumps(context['final_analyzer_report'])}
- Research Journey Summary: {json.dumps(context['research_history'])}

Task:
Synthesize a clear answer to the Initial Query based *only* on the provided extracted information and assessment. Create a concise research journey summary. List key sources if available in the extracted information.

Output Format:
Respond ONLY with a JSON object containing the final answer and summary. Do not include any explanatory text before or after the JSON.

{{
  "final_answer": "<Synthesized answer to the query>",
  "research_summary": "<Brief summary of the research steps taken>",
  "key_sources": ["<URL/Source 1>", "<URL/Source 2>"]
}}
"""
            
            response = call_llm(prompt)
            
            # Log the raw response for debugging
            debug("HITLOutputNode", f"Raw LLM response: {response[:100]}...", level=3)

            # Similar JSON parsing logic as in DecisionNode
            try:
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip() if json_end > json_start else response
                elif "```" in response:
                     json_start = response.find("```") + 3
                     json_end = response.find("```", json_start)
                     json_str = response[json_start:json_end].strip() if json_end > json_start else response
                elif "{" in response and "}" in response:
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    json_str = response[json_start:json_end].strip() if json_end > json_start else response
                else:
                    json_str = response

                debug("HITLOutputNode", f"Attempting to parse: {json_str[:100]}...", level=3)
                output = json.loads(json_str)
                
                if "final_answer" not in output:
                    raise ValueError("HITL output missing 'final_answer' field")
                
                return output

            except json.JSONDecodeError as e:
                debug_error("HITLOutputNode", f"Failed to parse JSON response: {e}")
                # Fallback: return the raw response as the answer
                return {"final_answer": response, "research_summary": "Failed to parse structured output.", "key_sources": []}
                
        except Exception as e:
            debug_error("HITLOutputNode", e)
            raise
    
    def post(self, shared, prep_res, exec_res):
        # Skip post-processing if execution was skipped
        if exec_res is None:
            debug("HITLOutputNode", "[OUTPUT] Skipped storing output.", level=2)
            return "default" # Proceed to feedback node
            
        # Store the final answer and details
        shared["final_answer_details"] = exec_res
        shared["final_answer"] = exec_res.get("final_answer", "Error: No answer generated.")
        shared["display_feedback"] = True # Enable the feedback node
        debug("HITLOutputNode", f"[OUTPUT] Stored final_answer_details, final_answer. Set display_feedback=True.", level=2)
        
        # Route to the feedback node
        return "default"

class HumanFeedbackNode(Node):
    """Node for processing human feedback on the research results."""
    
    def prep(self, shared):
        display = shared.get("display_feedback", False)
        answer = shared.get("final_answer")
        debug("HumanFeedbackNode", f"[INPUT] Checking conditions - display_feedback: {display}, final_answer exists: {answer is not None}", level=2)
        # Only process if we have a final answer to display
        if not display or not answer:
            return None
            
        debug("HumanFeedbackNode", f"[INPUT] Proceeding with final_answer display.", level=2)
        return answer
    
    def exec(self, final_answer):
        # Skip if prep returned None
        if final_answer is None:
            debug("HumanFeedbackNode", "Skipping execution (no final answer to display)")
            return None
        
        debug("HumanFeedbackNode", "Displaying final answer and collecting feedback")
        try:
            # Display the answer to the user
            print("\n" + "="*80)
            print(final_answer)
            print("="*80 + "\n")
            
            # Get feedback from the user
            print("Are you satisfied with this answer? (yes/no)")
            satisfaction = input("> ").strip().lower()
            
            if satisfaction in ["y", "yes"]:
                debug("HumanFeedbackNode", "User satisfied with answer")
                return {"satisfied": True}
            
            # If not satisfied, get more specific feedback
            debug("HumanFeedbackNode", "User not satisfied, collecting additional feedback")
            print("Please provide more specific feedback or additional information:")
            feedback = input("> ")
            
            return {
                "satisfied": False,
                "feedback": feedback
            }
        except Exception as e:
            debug_error("HumanFeedbackNode", e)
            raise
    
    def post(self, shared, prep_res, exec_res):
        # Skip if exec returned None (which means prep skipped)
        if exec_res is None:
            debug("HumanFeedbackNode", "[OUTPUT] Skipped feedback processing.", level=2)
            return "default" # Allow flow to end if no feedback processed
            
        # Reset display_feedback flag
        shared["display_feedback"] = False
        
        action = "end" # Default action is to end the flow
        if exec_res["satisfied"]:
            # Research complete
            print("Research task completed successfully.")
            action = "end"
        else:
            # Store feedback and reset for another loop
            feedback = exec_res["feedback"]
            debug("HumanFeedbackNode", f"User not satisfied, looping back to DecisionNode with feedback: {feedback[:50]}...", level=2)
            shared["human_feedback"] = feedback
            # Append feedback to original query for context in the next decision
            shared["original_query"] += f" [Feedback: {feedback}]"
            
            # Set action to loop back
            action = "continue_research"

        debug("HumanFeedbackNode", f"[OUTPUT] Reset display_feedback. Returning action: {action}", level=2)
        return action