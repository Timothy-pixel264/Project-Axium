import os
import time
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


class WebScraper:
    """Lightweight web scraper using Playwright for generic page scraping.

    Records videos of the scraping process for debugging and visualization.
    """

    def __init__(self):
        # Create videos directory if it doesn't exist
        self.videos_dir = Path("backend/videos")
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def scrape_url(self, url: str) -> Dict[str, Optional[str | List[str] | Dict]]:
        """Scrape a webpage and return its content with video recording.

        Args:
            url: The URL to scrape (must start with http:// or https://)

        Returns:
            Dictionary with keys:
            - url: The scraped URL
            - title: Page title from <title> tag
            - content: Dict with headings, paragraphs, and links
            - video_path: Relative path to the recording video
        """
        if sync_playwright is None:
            raise RuntimeError(
                "playwright is not installed. Install with `uv sync` or "
                "`pip install -r requirements.txt` and run `playwright install chromium`."
            )

        # Ensure URL is valid
        if not url.startswith("http://") and not url.startswith("https://"):
            raise ValueError(f"Invalid URL: {url}. Must start with http:// or https://")

        # Generate video filename from URL
        domain = urlparse(url).netloc.replace(".", "_")
        timestamp = int(time.time())
        video_path = self.videos_dir / f"scrape_web_{domain}_{timestamp}.webm"

        result: Dict[str, Optional[str | List[str] | Dict]] = {
            "url": url,
            "title": None,
            "content": {
                "headings": [],
                "paragraphs": [],
                "links": [],
            },
            "video_path": None,
        }

        with sync_playwright() as p:
            # Launch browser with headless=False for visibility
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(record_video_dir=str(self.videos_dir))
            page = context.new_page()

            try:
                # Step 1: Navigate to the URL
                print(f"[Step 1/3] Navigating to {url}...")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=30000)
                    print(f"✓ Page loaded successfully")
                except Exception as e:
                    error_msg = f"Failed to navigate to URL: {str(e)}"
                    print(f"✗ {error_msg}")
                    raise RuntimeError(error_msg)

                # Step 2: Scroll to load lazy-loaded content
                print(f"[Step 2/3] Scrolling to load all content...")
                try:
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    time.sleep(1)  # Wait for lazy-loaded content
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print(f"✓ All content loaded")
                except Exception as e:
                    error_msg = f"Failed to load content: {str(e)}"
                    print(f"✗ {error_msg}")
                    raise RuntimeError(error_msg)

                # Step 3: Extract page content
                print(f"[Step 3/3] Extracting page content...")
                try:
                    # Extract title
                    title_element = page.query_selector("title")
                    if title_element:
                        result["title"] = title_element.inner_text().strip()
                        print(f"  ✓ Found title: {result['title'][:50]}...")

                    # Extract headings
                    headings_elements = page.query_selector_all("h1, h2, h3, h4, h5, h6")
                    for heading in headings_elements:
                        text = heading.inner_text().strip()
                        if text and len(text) > 0:
                            result["content"]["headings"].append(text)
                    if result["content"]["headings"]:
                        print(f"  ✓ Found {len(result['content']['headings'])} headings")

                    # Extract paragraphs
                    paragraph_elements = page.query_selector_all("p")
                    for para in paragraph_elements:
                        text = para.inner_text().strip()
                        if text and len(text) > 0:
                            result["content"]["paragraphs"].append(text)
                    if result["content"]["paragraphs"]:
                        print(f"  ✓ Found {len(result['content']['paragraphs'])} paragraphs")

                    # Extract links
                    link_elements = page.query_selector_all("a")
                    for link in link_elements:
                        href = link.get_attribute("href")
                        text = link.inner_text().strip()
                        if href and text and len(text) > 0:
                            result["content"]["links"].append({
                                "text": text[:100],  # Limit text length
                                "href": href
                            })
                    if result["content"]["links"]:
                        print(f"  ✓ Found {len(result['content']['links'])} links")

                    print(f"✓ Content extraction completed successfully")
                except Exception as e:
                    error_msg = f"Error during content extraction: {str(e)}"
                    print(f"✗ {error_msg}")
                    raise RuntimeError(error_msg)

            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                # Re-raise to let caller handle
                raise
            finally:
                # Save the video recording
                video_file = page.video.path()
                if video_file:
                    try:
                        from shutil import move
                        if video_path and not video_path.exists():
                            move(str(video_file), str(video_path))
                            result["video_path"] = str(video_path.relative_to(Path.cwd()))
                            print(f"Video saved to: {video_path}")
                    except Exception as ve:
                        print(f"Warning: Failed to save video: {str(ve)}")

                context.close()
                browser.close()

        return result
