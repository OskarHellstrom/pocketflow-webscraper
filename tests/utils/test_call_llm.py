import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.call_llm import call_llm

class TestCallLLM(unittest.TestCase):

    @patch('utils.call_llm.genai.GenerativeModel')
    @patch('utils.call_llm.load_dotenv') # Mock load_dotenv
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"}) # Keep this for the success test
    def test_call_llm_success(self, mock_load_dotenv, mock_generative_model):
        """Test that call_llm successfully calls the Gemini API and returns the response"""
        # Setup the mock
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "This is a test response from the LLM."
        mock_model_instance.generate_content.return_value = mock_response
        
        # Call the function
        result = call_llm("Test prompt")
        
        # Assert the result
        self.assertEqual(result, "This is a test response from the LLM.")
        
        # Verify the mock was called with correct parameters
        mock_generative_model.assert_called_once_with("gemini-2.5-flash-preview-04-17")
        mock_model_instance.generate_content.assert_called_once()
    
    @patch('utils.call_llm.genai.GenerativeModel')
    @patch('utils.call_llm.load_dotenv') # Mock load_dotenv
    @patch('utils.call_llm.os.getenv', return_value=None) # Mock os.getenv to return None
    def test_call_llm_missing_api_key(self, mock_os_getenv, mock_load_dotenv, mock_generative_model):
        """Test that call_llm handles missing API key"""
        # Call the function with missing API key
        with patch('builtins.print') as mock_print:
            call_llm("Test prompt")
            
            # Verify warning was printed
            mock_print.assert_called_with("Warning: GOOGLE_API_KEY not found in environment variables")
    
    @patch('utils.call_llm.genai.GenerativeModel')
    @patch('utils.call_llm.load_dotenv') # Mock load_dotenv
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
    def test_call_llm_exception_handling(self, mock_load_dotenv, mock_generative_model):
        """Test that call_llm properly handles exceptions"""
        # Setup the mock to raise an exception
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        mock_model_instance.generate_content.side_effect = Exception("Test exception")
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result = call_llm("Test prompt")
            
            # Verify error was printed
            mock_print.assert_called_with("Error calling Google Gemini: Test exception")
            
            # Verify result contains error message
            self.assertEqual(result, "Error: Test exception")

if __name__ == '__main__':
    unittest.main() 