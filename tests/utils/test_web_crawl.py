import unittest
from unittest.mock import patch, MagicMock
import requests
import sys
import os

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.web_crawl import crawl_url

class TestWebCrawl(unittest.TestCase):

    @patch('utils.web_crawl.requests.get')
    def test_crawl_url_success(self, mock_get):
        """Test successful URL crawling"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Test Page</title>
            </head>
            <body>
                <h1>Test Content</h1>
                <p>This is a test paragraph.</p>
                <script>alert('This should be removed');</script>
                <style>.test { color: red; }</style>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Call the function
        result = crawl_url("https://example.com")
        
        # Assert the result
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["title"], "Test Page")
        self.assertEqual(result["status"], 200)
        self.assertIn("Test Content", result["content"])
        self.assertIn("This is a test paragraph", result["content"])
        
        # Script and style content should be removed
        self.assertNotIn("alert", result["content"])
        self.assertNotIn("color: red", result["content"])
    
    @patch('utils.web_crawl.requests.get')
    def test_crawl_url_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        # Setup mock to raise HTTP error
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        # Call the function with max_retries=1 to speed up test
        result = crawl_url("https://example.com", max_retries=1)
        
        # Assert the error result
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["title"], "Error")
        self.assertEqual(result["status"], 0)
        self.assertIn("Failed to crawl the URL", result["content"])
    
    @patch('utils.web_crawl.requests.get')
    def test_crawl_url_connection_error(self, mock_get):
        """Test handling of connection errors"""
        # Setup mock to raise connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Call the function with max_retries=1 to speed up test
        result = crawl_url("https://example.com", max_retries=1)
        
        # Assert the error result
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["title"], "Error")
        self.assertEqual(result["status"], 0)
        self.assertIn("Failed to crawl the URL", result["content"])

if __name__ == '__main__':
    unittest.main() 