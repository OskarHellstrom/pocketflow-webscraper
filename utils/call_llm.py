import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils.debug import debug, debug_error

# Load environment variables
load_dotenv()

# Learn more about calling the LLM: https://the-pocket.github.io/PocketFlow/utility_function/llm.html
def call_llm(prompt, model="gemini-2.5-flash-preview-04-17", temperature=0.6, max_tokens=4000):
    """
    Call Google Gemini to process a prompt and return a response.
    
    Args:
        prompt: The input prompt to send to the LLM
        model: The model to use (default: gemini-2.5-flash-preview-04-17)
        temperature: Controls randomness (lower = more deterministic)
        max_tokens: Maximum token limit for the response
        
    Returns:
        The LLM's response as a string
    """
    debug("LLM", f"Calling model {model} with temperature {temperature}", level=2)
    
    # Get API key from environment variables
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        debug_error("LLM", "GOOGLE_API_KEY not found in environment variables")
        print("Warning: GOOGLE_API_KEY not found in environment variables")
        api_key = "YOUR_API_KEY_HERE"  # Fallback for development
    
    # Configure the Google Generative AI client
    genai.configure(api_key=api_key)
    
    try:
        # Create a generative model
        model = genai.GenerativeModel(model)
        
        # Generate response
        debug("LLM", "Sending request to model", level=2)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        # Extract and return the response text
        debug("LLM", "Received response from model", level=2)
        return response.text
        
    except Exception as e:
        debug_error("LLM", f"Error calling Google Gemini: {e}")
        print(f"Error calling Google Gemini: {e}")
        return f"Error: {str(e)}"
    
if __name__ == "__main__":
    # Test the function
    test_prompt = "What is the meaning of life? Answer in one sentence."
    print(f"Prompt: {test_prompt}")
    print(f"Response: {call_llm(test_prompt)}")
