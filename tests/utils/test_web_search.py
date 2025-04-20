import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock load_dotenv before importing the module that uses it
with patch('utils.web_search.load_dotenv') as mock_load_dotenv:
    from utils.web_search import search_duckduckgo, search_google

class TestWebSearch(unittest.TestCase):

    @patch('utils.web_search.DDGS')
    def test_search_duckduckgo_success(self, mock_ddgs):
        """Test successful DuckDuckGo search"""
        # Setup mock
        mock_ddgs_instance = MagicMock()
        mock_ddgs.return_value = mock_ddgs_instance
        
        # Set up mock search results
        mock_results = [
            {
                "title": "Test Result 1",
                "href": "https://example.com/1",
                "body": "This is the first test result"
            },
            {
                "title": "Test Result 2",
                "href": "https://example.com/2",
                "body": "This is the second test result"
            }
        ]
        mock_ddgs_instance.text.return_value = mock_results
        
        # Call the function
        results = search_duckduckgo("test query", max_results=2)
        
        # Assert the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Test Result 1")
        self.assertEqual(results[0]["link"], "https://example.com/1")
        self.assertEqual(results[0]["snippet"], "This is the first test result")
        
        # Verify the mock was called correctly
        mock_ddgs_instance.text.assert_called_once_with("test query", max_results=2)
    
    @patch('utils.web_search.DDGS')
    def test_search_duckduckgo_exception(self, mock_ddgs):
        """Test DuckDuckGo search exception handling"""
        # Setup mock to raise an exception
        mock_ddgs_instance = MagicMock()
        mock_ddgs.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.side_effect = Exception("Search failed")
        
        # Call the function
        with patch('builtins.print') as mock_print:
            results = search_duckduckgo("test query")
            
            # Assert results contain error message
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Error performing search")
            self.assertIn("Search failed", results[0]["snippet"])
            
            # Verify error was printed
            mock_print.assert_called_with("Error in DuckDuckGo search: Search failed")
    
    @patch('utils.web_search.build')
    # Mock os.getenv specifically for this test case to return valid keys
    @patch('utils.web_search.os.getenv', side_effect=lambda key: {"GOOGLE_API_KEY": "test_key", "GOOGLE_CSE_ID": "test_cse"}.get(key))
    def test_search_google_success(self, mock_os_getenv, mock_build):
        """Test successful Google search"""
        # Setup mock for googleapiclient build
        mock_service = MagicMock()
        mock_cse = MagicMock()
        mock_list = MagicMock()
        mock_execute = MagicMock()
        
        mock_build.return_value = mock_service
        mock_service.cse.return_value = mock_cse
        mock_cse.list.return_value = mock_list
        mock_list.execute.return_value = {
            "items": [
                {
                    "title": "Google Result 1",
                    "link": "https://example.com/g1",
                    "snippet": "This is the first Google result"
                },
                {
                    "title": "Google Result 2",
                    "link": "https://example.com/g2",
                    "snippet": "This is the second Google result"
                }
            ]
        }
        
        # Call the function
        results = search_google("test query", max_results=2)
        
        # Assert the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Google Result 1")
        self.assertEqual(results[0]["link"], "https://example.com/g1")
        self.assertEqual(results[0]["snippet"], "This is the first Google result")
        
        # Verify the mocks were called correctly
        mock_os_getenv.assert_any_call("GOOGLE_API_KEY")
        mock_os_getenv.assert_any_call("GOOGLE_CSE_ID")
        mock_build.assert_called_once_with("customsearch", "v1", developerKey="test_key")
        mock_cse.list.assert_called_once_with(q="test query", cx="test_cse", num=2)
    
    # Mock os.getenv specifically for this test case to return None
    @patch('utils.web_search.os.getenv', side_effect=lambda key: None)
    def test_search_google_missing_credentials(self, mock_os_getenv):
        """Test Google search handling of missing API credentials"""
        # Call the function
        with patch('builtins.print') as mock_print:
            results = search_google("test query")

        # Assert the function returns the expected error structure
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Error performing search")
        self.assertIn("Missing Google API credentials", results[0]["snippet"])

        # Verify os.getenv was called for the keys
        mock_os_getenv.assert_any_call("GOOGLE_API_KEY")
        mock_os_getenv.assert_any_call("GOOGLE_CSE_ID")

        # Verify the error was printed via debug_error and print
        mock_print.assert_called_with("Error in Google search: Missing Google API credentials. Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.")

if __name__ == '__main__':
    unittest.main() 