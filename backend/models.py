from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class LinkedInProfile(BaseModel):
    """LinkedIn profile data structure"""
    name: str
    headline: Optional[str] = None
    bio: Optional[str] = None
    experience: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    education: Optional[List[str]] = None


class GameStatus(str, Enum):
    """Game status enumeration"""
    SETUP = "setup"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Player(BaseModel):
    """Player data structure"""
    profile: LinkedInProfile
    health: int = 100
    name: str


class GameState(BaseModel):
    """Game state structure"""
    game_id: str
    player1: Player
    player2: Player
    current_turn: int  # 1 or 2
    status: GameStatus
    last_roast: Optional[str] = None
    last_damage: Optional[int] = None
    winner: Optional[int] = None  # 1 or 2
    round_number: int = 1


class RoastRequest(BaseModel):
    """Request for generating a roast"""
    game_id: str
    player_number: int  # 1 or 2


class RoastResponse(BaseModel):
    """Response containing generated roast"""
    roast: str
    player_number: int


class ReviewRequest(BaseModel):
    """Request for reviewing a roast"""
    game_id: str
    roast: str
    target_player_number: int  # 1 or 2


class ReviewResponse(BaseModel):
    """Response containing roast review and damage"""
    damage: int
    reasoning: str
    roast: str


class StartGameRequest(BaseModel):
    """Request to start a new game"""
    player1_profile: LinkedInProfile
    player2_profile: LinkedInProfile


class StartGameResponse(BaseModel):
    """Response containing game ID"""
    game_id: str
    game_state: GameState







