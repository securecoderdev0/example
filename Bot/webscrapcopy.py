# web_scraper.py
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import random
import time
import json
import csv
import os

class WebScraper:
    def __init__(self, base_url: str, depth: int = 1):
        self.base_url = base_url
        self.depth = depth
        self.soup = None
        self.visited_urls = set()  # Keep track of visited URLs to avoid cycles
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/60.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.119 Mobile Safari/537.36',
        ]

    def fetch_page(self, url: Optional[str] = None) -> bool:
        """Fetches the HTML content of the page."""
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(url or self.base_url, headers=headers)
            response.raise_for_status()  # Check if the request was successful
            self.soup = BeautifulSoup(response.text, 'html.parser')
            return True
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return False

    def get_all_links(self) -> List[str]:
        """Extracts all links (anchor tags) from the page."""
        if self.soup is None:
            print("Page not fetched. Use fetch_page() first.")
            return []
        
        links = [a.get('href') for a in self.soup.find_all('a', href=True)]
        return [link for link in links if link.startswith(('http', 'https'))]  # Filter only valid URLs

    def get_all_images(self) -> List[str]:
        """Extracts all image URLs from the page."""
        if self.soup is None:
            print("Page not fetched. Use fetch_page() first.")
            return []
        
        images = [img.get('src') for img in self.soup.find_all('img', src=True)]
        return images

    def get_text(self, selector: str) -> str:
        """Extracts text based on a CSS selector."""
        if self.soup is None:
            print("Page not fetched. Use fetch_page() first.")
            return ""
        
        element = self.soup.select_one(selector)
        return element.get_text(strip=True) if element else ""

    def get_data_table(self, table_selector: str) -> List[Dict[str, str]]:
        """Extracts a data table based on the provided selector."""
        if self.soup is None:
            print("Page not fetched. Use fetch_page() first.")
            return []
        
        table_data = []
        table = self.soup.select_one(table_selector)
        if not table:
            print("No table found with the given selector.")
            return table_data

        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        for row in table.find_all('tr')[1:]:
            row_data = {headers[i]: td.get_text(strip=True) for i, td in enumerate(row.find_all('td'))}
            table_data.append(row_data)
        
        return table_data

    def get_metadata(self) -> Dict[str, str]:
        """Extracts meta tags content from the page."""
        if self.soup is None:
            print("Page not fetched. Use fetch_page() first.")
            return {}
        
        meta_data = {}
        for meta in self.soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                meta_data[name] = content
        return meta_data
    
    def filter_links(self, keyword: str) -> List[str]:
        """Filters links containing the specified keyword."""
        return [link for link in self.get_all_links() if keyword in link]

    def save_to_json(self, data: Dict, filename: str):
        """Saves the scraped data to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def save_to_csv(self, data: List[Dict[str, str]], filename: str):
        """Saves the scraped data to a CSV file."""
        keys = data[0].keys() if data else []
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    def scrape_recursive(self, url: str, current_depth: int):
        """Recursively scrape pages to a specified depth."""
        if current_depth > self.depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)

        if self.fetch_page(url):
            print(f"Scraping: {url}")
            time.sleep(1)  # Sleep to avoid overwhelming the server
            
            # Collect data
            data = {
                'url': url,
                'links': self.get_all_links(),
                'images': self.get_all_images(),
                'metadata': self.get_metadata(),
            }

            # Save data to JSON
            self.save_to_json(data, f"scraped_data_{current_depth}.json")
            print(f"Data saved for {url}")

            # Recursively scrape each link found on this page
            for link in self.get_all_links():
                self.scrape_recursive(link, current_depth + 1)

# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Web Scraper')
    parser.add_argument('url', type=str, help='Base URL to scrape')
    parser.add_argument('--depth', type=int, default=1, help='Depth of recursion for scraping')

    args = parser.parse_args()

    # Initialize the scraper with a base URL
    scraper = WebScraper(args.url, depth=args.depth)

    # Start scraping
    scraper.scrape_recursive(args.url, 1)
