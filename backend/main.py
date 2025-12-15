from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import (
    StartGameRequest, StartGameResponse,
    RoastRequest, RoastResponse,
    ReviewRequest, ReviewResponse,
    GameState
)
from game_manager import GameManager
from ai_service import AIService

app = FastAPI(title="LinkedIn Roast Battle API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
game_manager = GameManager()
ai_service = AIService()


@app.get("/")
def root():
    return {"message": "LinkedIn Roast Battle API"}


@app.post("/api/game/start", response_model=StartGameResponse)
def start_game(request: StartGameRequest):
    """Initialize a new game with two LinkedIn profiles"""
    try:
        game_id = game_manager.create_game(
            request.player1_profile,
            request.player2_profile
        )
        game_state = game_manager.get_game(game_id)
        
        return StartGameResponse(
            game_id=game_id,
            game_state=game_state
        )
    except Exception as e:
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
    """Generate a roast for the current player"""
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
    else:
        attacker_profile = game_state.player2.profile
        target_profile = game_state.player1.profile
    
    try:
        roast = ai_service.generate_roast(attacker_profile, target_profile)
        game_manager.update_last_roast(game_id, roast)
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)







