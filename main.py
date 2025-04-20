import os
from dotenv import load_dotenv
from flow import research_flow
from utils.debug import debug, debug_error

def main():
    """Main entry point for the web research agent."""
    print("="*80)
    print("Dynamic Web Research Agent")
    print("="*80)
    
    # Load environment variables
    load_dotenv()
    
    # Set default debug level if not in environment
    debug_level = os.getenv("DEBUG_LEVEL", "1")
    os.environ["DEBUG_LEVEL"] = debug_level
    
    # Show debug status
    print(f"Debug level: {debug_level}")
    debug("Main", "Starting the research agent", level=1)
    
    # Check for required API keys
    if not os.getenv("GOOGLE_API_KEY"):
        debug_error("Main", "GOOGLE_API_KEY not found in environment variables")
        print("Warning: GOOGLE_API_KEY not found in environment variables")
        print("Please set this in your .env file to use the agent")
    
    # Initialize shared memory
    shared = {}
    
    try:
        # Run the research flow
        debug("Main", "Starting research flow", level=1)
        research_flow.run(shared)
        
        debug("Main", "Research flow completed successfully", level=1)
        print("\nResearch flow completed")
    
    except KeyboardInterrupt:
        debug_error("Main", "Research flow interrupted by user")
        print("\nResearch flow interrupted by user")
    
    except Exception as e:
        debug_error("Main", f"Unhandled error occurred: {e}")
        print(f"\nError occurred: {e}")

if __name__ == "__main__":
    main()