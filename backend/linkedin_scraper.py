import os
import re
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]


class LinkedInScraper:
    """Lightweight LinkedIn scraper using Playwright with Google OAuth login.

    Requires env vars:
    - LI_EMAIL: Google account email (defaults to timothywongjj@gmail.com)
    - LI_PASSWORD: Google account password

    Uses Google OAuth instead of LinkedIn credentials for more reliable authentication.
    Records videos of the scraping process for debugging and visualization.
    """

    def __init__(self):
        self.email = os.getenv("LI_EMAIL", "timothywongjj@gmail.com")
        self.password = os.getenv("LI_PASSWORD")
        if not self.password:
            raise RuntimeError("LI_PASSWORD must be set for LinkedIn scraping.")

        # Create videos directory if it doesn't exist
        self.videos_dir = Path("backend/videos")
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def scrape_profile(self, profile_url: str) -> Dict[str, Optional[List[str] | str]]:
        """Scrape a LinkedIn profile page and return profile sections with video recording.

        NOTE: This is a best-effort parser; LinkedIn DOM changes often.
        Uses Playwright to login and scrape the provided profile URL.
        Records video of the scraping process for visualization.
        """
        if sync_playwright is None:
            raise RuntimeError(
                "playwright is not installed. Install with `uv sync` or "
                "`pip install -r requirements.txt` and run `playwright install chromium`."
            )

        # Ensure URL is clean
        cleaned_url = profile_url.split("?")[0].rstrip("/")
        if not cleaned_url.startswith("http"):
            cleaned_url = f"https://www.linkedin.com/in/{cleaned_url}"

        # Generate video filename from profile URL
        profile_name = cleaned_url.split("/in/")[-1].replace("/", "_")
        video_path = self.videos_dir / f"scrape_{profile_name}_{int(__import__('time').time())}.webm"

        result: Dict[str, Optional[List[str] | str]] = {
            "headline": None,
            "bio": None,
            "experience": [],
            "skills": [],
            "education": [],
            "video_path": None,
            "scraping_errors": [],
        }

        with sync_playwright() as p:
            # Launch browser with headless=False for visibility and debugging
            browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(record_video_dir=str(self.videos_dir))
            page = context.new_page()

            try:
                # Step 1: Navigate to LinkedIn login page
                print(f"[Step 1/7] Navigating to LinkedIn login page...")
                try:
                    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
                    page.wait_for_load_state("networkidle")
                    print(f"✓ Login page loaded")
                except Exception as e:
                    error_msg = f"Failed to navigate to LinkedIn login page: {str(e)}"
                    print(f"✗ {error_msg}")
                    result["scraping_errors"].append({
                        "stage": "url_navigation",
                        "step": 1,
                        "error": error_msg,
                        "attempted_action": "Navigate to https://www.linkedin.com/login",
                    })
                    raise

                # Step 2: Look for Google sign-in button and click it
                print(f"[Step 2/6] Looking for 'Continue with Google' button...")
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                    time.sleep(1)

                    # Find the "Continue with Google" button
                    google_button = page.locator('button:has-text("Continue with Google")').first

                    if not google_button or not google_button.is_visible():
                        # Try alternative selector
                        google_button = page.locator('[aria-label*="Google"], button:has-text("Google")').first

                    if google_button and google_button.is_visible():
                        print(f"✓ Google button found and visible")
                        # Listen for new page (popup/tab) before clicking
                        with context.expect_page() as new_page_info:
                            google_button.click()
                            print(f"✓ Clicked 'Continue with Google' button")

                        google_page = new_page_info.value
                        print(f"✓ New Google tab opened: {google_page.url}")
                    else:
                        raise RuntimeError("'Continue with Google' button not found or not visible")
                except Exception as e:
                    error_msg = f"Failed to find or click Google sign-in button: {str(e)}"
                    print(f"✗ {error_msg}")
                    result["scraping_errors"].append({
                        "stage": "google_button_detection",
                        "step": 2,
                        "error": error_msg,
                        "attempted_action": "Find and click 'Continue with Google' button",
                    })
                    raise

                # Step 3: Wait for Google login page to load
                print(f"[Step 3/6] Waiting for Google authentication page to load...")
                try:
                    google_page.wait_for_load_state("domcontentloaded", timeout=15000)
                    time.sleep(2)
                    print(f"✓ Google login page loaded: {google_page.url}")
                except Exception as e:
                    error_msg = f"Failed to load Google authentication page: {str(e)}"
                    print(f"✗ {error_msg}")
                    result["scraping_errors"].append({
                        "stage": "google_page_load",
                        "step": 3,
                        "error": error_msg,
                        "attempted_action": "Wait for Google authentication page to load",
                    })
                    raise

                # Step 4: Enter Google credentials and authenticate
                print(f"[Step 4/6] Entering Google credentials...")
                try:
                    # Wait for email input to be available
                    google_page.wait_for_selector('input[type="email"]', timeout=10000)
                    time.sleep(1)

                    # Find and fill email input
                    email_input = google_page.locator('input[type="email"]').first
                    if email_input:
                        email_input.fill(self.email)
                        print(f"✓ Google email entered: {self.email}")
                        time.sleep(0.5)
                        email_input.press('Enter')
                        time.sleep(2)

                    # Wait for password input to appear
                    google_page.wait_for_selector('input[type="password"]', timeout=10000)
                    time.sleep(1)

                    # Find and fill password input
                    password_input = google_page.locator('input[type="password"]').first
                    if password_input:
                        password_input.fill(self.password)
                        print(f"✓ Google password entered")
                        time.sleep(0.5)
                        password_input.press('Enter')
                        time.sleep(3)

                    # Wait for Google auth to complete
                    google_page.wait_for_load_state("networkidle", timeout=15000)
                    print(f"✓ Google authentication completed")
                except Exception as e:
                    error_msg = f"Failed during Google authentication: {str(e)}"
                    print(f"✗ {error_msg}")
                    result["scraping_errors"].append({
                        "stage": "google_authentication",
                        "step": 4,
                        "error": error_msg,
                        "attempted_action": "Enter Google credentials and authenticate",
                    })
                    raise

                # Step 5: Wait for redirect back to LinkedIn
                print(f"[Step 5/6] Waiting for LinkedIn authentication to complete...")
                try:
                    # The Google tab should close/redirect back to LinkedIn
                    # Switch back to main LinkedIn page if needed
                    page.wait_for_url("**linkedin.com**", timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=30000)
                    time.sleep(2)
                    print(f"✓ Successfully authenticated and returned to LinkedIn")
                except Exception as e:
                    error_msg = f"Failed to redirect back to LinkedIn after Google auth: {str(e)}"
                    print(f"✗ {error_msg}")
                    result["scraping_errors"].append({
                        "stage": "linkedin_redirect",
                        "step": 5,
                        "error": error_msg,
                        "attempted_action": "Wait for redirect to LinkedIn after Google authentication",
                        "possible_causes": ["Authentication failed", "Network timeout", "2FA required"],
                    })
                    raise

                # Step 6: Navigate to the target profile
                print(f"[Step 6/6] Navigating to profile: {cleaned_url}")
                try:
                    page.goto(cleaned_url, wait_until="domcontentloaded")
                    page.wait_for_load_state("networkidle", timeout=30000)
                    print(f"✓ Profile page loaded")

                    # Scroll to load lazy-loaded content
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    time.sleep(1)  # Wait for lazy-loaded content
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print(f"✓ All content loaded")
                except Exception as e:
                    error_msg = f"Failed to load profile page: {str(e)}"
                    print(f"✗ {error_msg}")
                    result["scraping_errors"].append({
                        "stage": "profile_navigation",
                        "step": 6,
                        "error": error_msg,
                        "attempted_action": f"Navigate to profile URL: {cleaned_url}",
                        "possible_causes": ["Profile is private", "Profile does not exist", "Profile URL is invalid", "Access denied"],
                    })
                    raise

                def grab_text(selector: str, field_name: str = "") -> Optional[str]:
                    """Extract text from first matching element with logging."""
                    el = page.query_selector(selector)
                    if not el:
                        return None
                    text = el.inner_text().strip()
                    if text:
                        if field_name:
                            print(f"  ✓ Found {field_name}: {text[:50]}...")
                        return text
                    return None

                def grab_list(selectors: List[str], field_name: str = "", limit: int = 20) -> List[str]:
                    """Extract text from multiple elements with logging."""
                    collected: List[str] = []
                    for sel in selectors:
                        nodes = page.query_selector_all(sel)
                        for node in nodes:
                            txt = node.inner_text().strip()
                            if txt and len(txt) > 0:
                                # Clean up whitespace
                                cleaned_txt = re.sub(r"\s+", " ", txt)
                                if cleaned_txt not in collected:  # Avoid duplicates
                                    collected.append(cleaned_txt)
                            if len(collected) >= limit:
                                break
                        if collected:
                            break
                    if collected and field_name:
                        print(f"  ✓ Found {field_name}: {len(collected)} items")
                    return collected

                # Scraping section with detailed logging
                print(f"\nScraping profile content...")

                try:
                    # Extract headline (profile title) - using stable data-test-id selectors
                    headline_selectors = [
                        "div[data-test-id='topcard-title']",
                        "h1[data-test-id='top-card-attestation-tests-profile-headline']",
                        "h2.text-heading-xlarge.inline",
                        "div.text-body-medium.break-words",
                    ]
                    for sel in headline_selectors:
                        result["headline"] = grab_text(sel, "Headline")
                        if result["headline"]:
                            break
                    if not result["headline"]:
                        print(f"  ⚠ Headline not found")
                        result["scraping_errors"].append({
                            "stage": "scraping_headline",
                            "error": "Could not extract headline from profile",
                            "attempted_selectors": headline_selectors,
                        })

                    # Extract about/bio section
                    bio_selectors = [
                        "div[data-test-id='about']",
                        "p[data-test-id='about-section']",
                        "div.inline-show-more-text div",
                    ]
                    for sel in bio_selectors:
                        result["bio"] = grab_text(sel, "Bio")
                        if result["bio"]:
                            break
                    if not result["bio"]:
                        print(f"  ⚠ Bio not found")
                        result["scraping_errors"].append({
                            "stage": "scraping_bio",
                            "error": "Could not extract bio from profile",
                            "attempted_selectors": bio_selectors,
                        })

                    # Extract experience using stable data-* selectors
                    experience_selectors = [
                        "li[data-test-id*='experience']",
                        "section[data-section='experience'] li",
                        "section#experience-section li",
                    ]
                    result["experience"] = grab_list(experience_selectors, "Experience entries", limit=10)
                    if not result["experience"]:
                        print(f"  ⚠ Experience not found")
                        result["scraping_errors"].append({
                            "stage": "scraping_experience",
                            "error": "Could not extract experience from profile",
                            "attempted_selectors": experience_selectors,
                        })

                    # Extract education using stable data-* selectors
                    education_selectors = [
                        "li[data-test-id*='education']",
                        "section[data-section='education'] li",
                        "section#education-section li",
                    ]
                    result["education"] = grab_list(education_selectors, "Education entries", limit=8)
                    if not result["education"]:
                        print(f"  ⚠ Education not found")
                        result["scraping_errors"].append({
                            "stage": "scraping_education",
                            "error": "Could not extract education from profile",
                            "attempted_selectors": education_selectors,
                        })

                    # Extract skills using stable data-* selectors
                    skills_selectors = [
                        "li[data-test-id*='skill-item']",
                        "section[data-section='skills'] li",
                        "section.pv-profile-section.pv-skill-categories-section li",
                    ]
                    result["skills"] = grab_list(skills_selectors, "Skills", limit=15)
                    if not result["skills"]:
                        print(f"  ⚠ Skills not found")
                        result["scraping_errors"].append({
                            "stage": "scraping_skills",
                            "error": "Could not extract skills from profile",
                            "attempted_selectors": skills_selectors,
                        })

                    print(f"✓ Scraping completed successfully")
                except Exception as e:
                    error_msg = f"Error during scraping data extraction: {str(e)}"
                    print(f"✗ {error_msg}")
                    result["scraping_errors"].append({
                        "stage": "scraping_error",
                        "error": error_msg,
                    })
                    raise

            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                # Don't re-raise - let the result with errors be returned to the frontend
                # so the user can see the detailed error logs
                pass
            finally:
                # Save the video recording
                video_file = page.video.path()
                if video_file:
                    try:
                        # Move video to final location
                        from shutil import move
                        if video_path and not video_path.exists():
                            move(str(video_file), str(video_path))
                            result["video_path"] = str(video_path.relative_to(Path.cwd()))
                            print(f"Video saved to: {video_path}")
                    except Exception as ve:
                        print(f"Warning: Failed to save video: {str(ve)}")

                context.close()
                browser.close()

        # If we failed to scrape anything meaningful AND have no errors logged, raise an error
        has_headline = bool(result.get("headline"))
        has_bio = bool(result.get("bio"))
        has_lists = any(
            bool(result.get(key)) for key in ("experience", "skills", "education")
        )
        has_errors = bool(result.get("scraping_errors")) and len(result.get("scraping_errors", [])) > 0

        if not (has_headline or has_bio or has_lists):
            if has_errors:
                # We have errors logged, return them so the frontend can display them
                return result
            else:
                # No data and no errors - something went wrong silently
                raise RuntimeError(
                    f"LinkedIn scrape returned empty content for: {cleaned_url}. "
                    "Profile may be private, restricted, or the URL may be invalid."
                )

        return result

