import requests
from bs4 import BeautifulSoup
import time
import random
from utils.debug import debug, debug_error

def crawl_url(url, max_retries=3):
    """
    Crawl a specific URL and extract the text content.
    
    Args:
        url: The URL to crawl
        max_retries: Maximum number of retry attempts
        
    Returns:
        Extracted text content from the webpage
    """
    debug("WebCrawler", f"Crawling URL: {url} (max_retries={max_retries})")
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Add a small delay to be courteous to the website
            time.sleep(1)
            
            # Make the request
            debug("WebCrawler", f"Making request (attempt {retry_count + 1})", level=2)
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the HTML content
            debug("WebCrawler", "Parsing HTML content", level=2)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Extract text content
            text = soup.get_text(separator='\n')
            
            # Process text to remove excessive whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Extract title if available
            title = soup.title.string if soup.title else "No title found"
            
            # Create a structured response
            result = {
                "url": url,
                "title": title,
                "content": text,
                "status": response.status_code
            }
            
            debug("WebCrawler", f"Successfully crawled URL: {url} (status={response.status_code})")
            return result
            
        except requests.exceptions.RequestException as e:
            retry_count += 1
            debug_error("WebCrawler", f"Error crawling {url} (attempt {retry_count}/{max_retries}): {e}")
            print(f"Error crawling {url}: {e}")
            time.sleep(2 * retry_count)  # Exponential backoff
    
    # Return an error message if all retries failed
    debug_error("WebCrawler", f"Failed to crawl the URL after {max_retries} attempts")
    return {
        "url": url,
        "title": "Error",
        "content": f"Failed to crawl the URL after {max_retries} attempts",
        "status": 0
    }

# Simple test function
if __name__ == "__main__":
    test_url = "https://en.wikipedia.org/wiki/Web_scraping"
    result = crawl_url(test_url)
    
    print(f"Title: {result['title']}")
    print(f"Status: {result['status']}")
    print(f"Content preview: {result['content'][:500]}...") 