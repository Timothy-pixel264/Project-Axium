import requests
from typing import Dict, Optional, List
from pathlib import Path
import time


class WikipediaScraper:
    """Lightweight Wikipedia scraper using the official MediaWiki API.

    Extracts article content without authentication.
    Records article metadata for roasting.
    """

    def __init__(self):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikiRoastBattle/1.0 (Educational Game)'
        })

    def scrape_article(self, url_or_title: str) -> Dict[str, Optional[str | List[str]]]:
        """Scrape a Wikipedia article using MediaWiki API.

        Args:
            url_or_title: Either a Wikipedia URL or article title

        Returns:
            Dictionary with keys:
            - title: Article title
            - content: Main article text
            - intro: Article introduction/lead section
            - headings: List of section headings
            - image_url: URL to article's main image if available
            - categories: List of article categories
            - error: Error message if scraping failed
        """
        try:
            # Extract title from URL if needed
            title = self._extract_title(url_or_title)
            if not title:
                raise ValueError(f"Could not extract article title from: {url_or_title}")

            # Get article content
            params = {
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'extracts|pageimages|categories',
                'explaintext': True,
                'exintro': False,
                'piprop': 'original',
                'pithumbsize': 400,
                'cmlimit': 50
            }

            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract page data
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                raise ValueError(f"Article not found: {title}")

            page_id = next(iter(pages.keys()))
            page = pages[page_id]

            # Check for redirect or missing page
            if 'missing' in page:
                raise ValueError(f"Article does not exist: {title}")

            # Extract content
            result = {
                'title': page.get('title', title),
                'content': page.get('extract', ''),
                'intro': self._extract_intro(page.get('extract', '')),
                'image_url': page.get('pageimage', {}).get('source') if page.get('pageimage') else None,
                'categories': [cat['title'].replace('Category:', '') for cat in page.get('categories', [])],
                'headings': self._extract_headings(page.get('extract', '')),
                'error': None
            }

            return result

        except Exception as e:
            error_msg = f"Failed to scrape Wikipedia article: {str(e)}"
            print(f"✗ {error_msg}")
            return {
                'title': None,
                'content': None,
                'intro': None,
                'image_url': None,
                'categories': [],
                'headings': [],
                'error': error_msg
            }

    def _extract_title(self, url_or_title: str) -> Optional[str]:
        """Extract Wikipedia article title from URL or validate title."""
        if url_or_title.startswith('http'):
            # Extract title from URL: https://en.wikipedia.org/wiki/Article_Title
            try:
                title = url_or_title.split('/wiki/')[-1]
                return title.replace('_', ' ')
            except Exception:
                return None
        else:
            # Assume it's already a title
            return url_or_title

    def _extract_intro(self, content: str) -> Optional[str]:
        """Extract the introduction (first paragraph) from article content."""
        if not content:
            return None

        # Split by double newline to get first section
        sections = content.split('\n\n')
        if sections:
            intro = sections[0]
            # Limit to reasonable length
            if len(intro) > 500:
                intro = intro[:500] + '...'
            return intro
        return None

    def _extract_headings(self, content: str) -> List[str]:
        """Extract section headings from article content."""
        if not content:
            return []

        headings = []
        lines = content.split('\n')

        for line in lines:
            # MediaWiki extracts often have == Section == format
            if line.startswith('==') and line.endswith('=='):
                heading = line.strip('= ').strip()
                if heading:
                    headings.append(heading)

        return headings[:15]  # Limit to first 15 headings

    def validate_url(self, url: str) -> bool:
        """Check if URL is a valid Wikipedia article URL."""
        if not url.startswith('https://') and not url.startswith('http://'):
            return False
        if 'wikipedia.org' not in url:
            return False
        if '/wiki/' not in url:
            return False
        return True
