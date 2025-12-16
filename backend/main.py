from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from models import (
    StartGameRequest, StartGameResponse,
    RoastRequest, RoastResponse,
    ReviewRequest, ReviewResponse,
    GameState,
    ScrapeRequest, ScrapeResponse,
    LinkedInProfile, WikipediaArticle
)
from game_manager import GameManager
from ai_service import AIService
from linkedin_scraper import LinkedInScraper
from web_scraper import WebScraper
from wikipedia_scraper import WikipediaScraper
import re

app = FastAPI(title="LinkedIn Roast Battle API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve videos directory for scraped profile recordings
videos_path = Path(__file__).parent / "videos"
videos_path.mkdir(parents=True, exist_ok=True)
app.mount("/videos", StaticFiles(directory=str(videos_path)), name="videos")

# Initialize services
game_manager = GameManager()
ai_service = AIService()
scraper: LinkedInScraper | None = None


def get_scraper() -> LinkedInScraper:
    global scraper
    if scraper is None:
        scraper = LinkedInScraper()
    return scraper


@app.get("/")
def root():
    return {"message": "LinkedIn Roast Battle API"}


@app.post("/api/game/start", response_model=StartGameResponse)
def start_game(request: StartGameRequest):
    """Initialize a new game with two LinkedIn profiles or Wikipedia articles"""
    try:
        # Enrich profiles via scraping if a URL is provided in bio
        linkedin_scraper = None
        try:
            linkedin_scraper = get_scraper()
        except Exception as e:
            # LinkedIn scraper is optional; log and continue without enrichment
            print(f"LinkedIn scraper unavailable: {e}")

        p1 = request.player1_profile
        p2 = request.player2_profile

        # Process Player 1 profile
        if hasattr(p1, 'bio') and p1.bio:
            # Check if bio looks like it's intended to be a URL
            if p1.bio.startswith("http") or "linkedin.com" in p1.bio.lower() or "wikipedia.org" in p1.bio.lower():
                try:
                    if "wikipedia.org" in p1.bio.lower():
                        # Scrape Wikipedia article
                        wiki_scraper = WikipediaScraper()
                        scraped = wiki_scraper.scrape_article(p1.bio)
                        if scraped.get("error"):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Failed to scrape Player 1's Wikipedia article: {scraped.get('error')}"
                            )
                        p1 = WikipediaArticle(
                            title=scraped.get("title") or p1.name,
                            content=scraped.get("content", ""),
                            intro=scraped.get("intro"),
                            headings=scraped.get("headings"),
                            image_url=scraped.get("image_url"),
                            categories=scraped.get("categories"),
                            video_path=scraped.get("video_path"),
                            scraping_errors=scraped.get("scraping_errors"),
                        )
                    elif "linkedin.com" in p1.bio.lower():
                        # Scrape LinkedIn profile
                        if not linkedin_scraper:
                            raise HTTPException(
                                status_code=500,
                                detail="LinkedIn scraper is not available. Please check the server configuration."
                            )
                        scraped = linkedin_scraper.scrape_profile(p1.bio)
                        p1 = type(p1)(
                            name=p1.name,
                            headline=scraped.get("headline") or p1.headline,
                            bio=scraped.get("bio") or p1.bio,
                            experience=scraped.get("experience") or p1.experience,
                            skills=scraped.get("skills") or p1.skills,
                            education=scraped.get("education") or p1.education,
                            video_path=scraped.get("video_path"),
                            scraping_errors=scraped.get("scraping_errors"),
                        )
                except RuntimeError as e:
                    # Scrape failed or returned empty - raise a user-friendly error
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to scrape Player 1's profile: {str(e)}. The profile may be empty, private, or the URL may be invalid."
                    )
                except Exception as e:
                    # Unexpected scraping error
                    if isinstance(e, HTTPException):
                        raise
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error scraping Player 1's profile: {str(e)}"
                    )

        # Process Player 2 profile
        if hasattr(p2, 'bio') and p2.bio:
            # Check if bio looks like it's intended to be a URL
            if p2.bio.startswith("http") or "linkedin.com" in p2.bio.lower() or "wikipedia.org" in p2.bio.lower():
                try:
                    if "wikipedia.org" in p2.bio.lower():
                        # Scrape Wikipedia article
                        wiki_scraper = WikipediaScraper()
                        scraped = wiki_scraper.scrape_article(p2.bio)
                        if scraped.get("error"):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Failed to scrape Player 2's Wikipedia article: {scraped.get('error')}"
                            )
                        p2 = WikipediaArticle(
                            title=scraped.get("title") or p2.name,
                            content=scraped.get("content", ""),
                            intro=scraped.get("intro"),
                            headings=scraped.get("headings"),
                            image_url=scraped.get("image_url"),
                            categories=scraped.get("categories"),
                            video_path=scraped.get("video_path"),
                            scraping_errors=scraped.get("scraping_errors"),
                        )
                    elif "linkedin.com" in p2.bio.lower():
                        # Scrape LinkedIn profile
                        if not linkedin_scraper:
                            raise HTTPException(
                                status_code=500,
                                detail="LinkedIn scraper is not available. Please check the server configuration."
                            )
                        scraped = linkedin_scraper.scrape_profile(p2.bio)
                        p2 = type(p2)(
                            name=p2.name,
                            headline=scraped.get("headline") or p2.headline,
                            bio=scraped.get("bio") or p2.bio,
                            experience=scraped.get("experience") or p2.experience,
                            skills=scraped.get("skills") or p2.skills,
                            education=scraped.get("education") or p2.education,
                            video_path=scraped.get("video_path"),
                            scraping_errors=scraped.get("scraping_errors"),
                        )
                except RuntimeError as e:
                    # Scrape failed or returned empty - raise a user-friendly error
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to scrape Player 2's profile: {str(e)}. The profile may be empty, private, or the URL may be invalid."
                    )
                except Exception as e:
                    # Unexpected scraping error
                    if isinstance(e, HTTPException):
                        raise
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error scraping Player 2's profile: {str(e)}"
                    )

        game_id = game_manager.create_game(
            p1,
            p2
        )
        game_state = game_manager.get_game(game_id)

        return StartGameResponse(
            game_id=game_id,
            game_state=game_state
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error starting game: {str(e)}")


@app.get("/api/game/{game_id}", response_model=GameState)
def get_game_state(game_id: str):
    """Get current game state"""
    game_state = game_manager.get_game(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_state


@app.post("/api/game/{game_id}/roast", response_model=RoastResponse)
def generate_roast(game_id: str, request: RoastRequest):
    """Generate and automatically judge a roast for the current player.

    This endpoint generates a roast and immediately applies AI judgment,
    automatically dealing damage to the opponent and advancing the turn.
    """
    game_state = game_manager.get_game(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")

    if game_state.status.value != "in_progress":
        raise HTTPException(status_code=400, detail="Game is not in progress")

    # Verify it's the correct player's turn
    if request.player_number != game_state.current_turn:
        raise HTTPException(
            status_code=400,
            detail=f"It's not player {request.player_number}'s turn"
        )

    # Determine attacker and target profiles
    if request.player_number == 1:
        attacker_profile = game_state.player1.profile
        target_profile = game_state.player2.profile
        opponent_player_number = 2
    else:
        attacker_profile = game_state.player2.profile
        target_profile = game_state.player1.profile
        opponent_player_number = 1

    try:
        # Step 1: Generate roast
        roast = ai_service.generate_roast(attacker_profile, target_profile)

        # Step 2: Automatically judge the roast
        review_result = ai_service.review_roast(roast, target_profile)
        damage = review_result["damage"]
        reasoning = review_result["reasoning"]

        # Step 3: Apply damage to opponent
        game_manager.apply_damage(game_id, opponent_player_number, damage)
        game_manager.update_last_roast(game_id, roast, damage)

        # Step 4: Move to next turn if game is still in progress
        updated_game = game_manager.get_game(game_id)
        if updated_game and updated_game.status.value == "in_progress":
            game_manager.next_turn(game_id)

        return RoastResponse(
            roast=roast,
            player_number=request.player_number
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating roast: {str(e)}")


@app.post("/api/game/{game_id}/review", response_model=ReviewResponse)
def review_roast(game_id: str, request: ReviewRequest):
    """Review a roast and calculate damage"""
    game_state = game_manager.get_game(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game_state.status.value != "in_progress":
        raise HTTPException(status_code=400, detail="Game is not in progress")
    
    # Determine target profile
    if request.target_player_number == 1:
        target_profile = game_state.player1.profile
        damage_to_player = 1
    else:
        target_profile = game_state.player2.profile
        damage_to_player = 2
    
    try:
        review_result = ai_service.review_roast(request.roast, target_profile)
        damage = review_result["damage"]
        reasoning = review_result["reasoning"]
        
        # Apply damage
        game_manager.apply_damage(game_id, damage_to_player, damage)
        game_manager.update_last_roast(game_id, request.roast, damage)
        
        # Move to next turn if game is still in progress
        updated_game = game_manager.get_game(game_id)
        if updated_game and updated_game.status.value == "in_progress":
            game_manager.next_turn(game_id)
        
        return ReviewResponse(
            damage=damage,
            reasoning=reasoning,
            roast=request.roast
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reviewing roast: {str(e)}")


def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = r'^https?:\/\/.+\..+'
    return bool(re.match(url_pattern, url))


@app.post("/api/scrape", response_model=ScrapeResponse)
def scrape_webpage(request: ScrapeRequest):
    """Scrape a webpage, LinkedIn profile, or Wikipedia article and return its content"""
    # Validate URL format
    if not validate_url(request.url):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL format. Please enter a valid URL starting with http:// or https://"
        )

    try:
        # Check if this is a Wikipedia article URL
        if "wikipedia.org" in request.url.lower():
            # Use Wikipedia scraper for Wikipedia article URLs
            scraper = WikipediaScraper()
            result = scraper.scrape_article(request.url)

            if result.get("error"):
                raise HTTPException(
                    status_code=400,
                    detail=result.get("error")
                )

            return ScrapeResponse(
                url=request.url,
                title=result.get("title"),
                content={
                    "intro": [result.get("intro")] if result.get("intro") else [],
                    "headings": result.get("headings", []),
                    "categories": result.get("categories", []),
                    "content_preview": [result.get("content", "")[:500]] if result.get("content") else []
                },
                video_path=None  # Wikipedia scraper doesn't use video recording
            )
        # Check if this is a LinkedIn profile URL
        elif "linkedin.com" in request.url.lower():
            # Use LinkedIn scraper for LinkedIn profile URLs
            scraper = get_scraper()
            result = scraper.scrape_profile(request.url)

            return ScrapeResponse(
                url=request.url,
                title=result.get("headline"),
                content={
                    "bio": [result.get("bio")] if result.get("bio") else [],
                    "experience": result.get("experience", []),
                    "education": result.get("education", []),
                    "skills": result.get("skills", [])
                },
                video_path=result.get("video_path")
            )
        else:
            # Use generic web scraper for other websites
            scraper = WebScraper()
            result = scraper.scrape_url(request.url)

            return ScrapeResponse(
                url=result.get("url"),
                title=result.get("title"),
                content=result.get("content"),
                video_path=result.get("video_path")
            )
    except ValueError as e:
        # URL validation error
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except RuntimeError as e:
        # Scraping error
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)







