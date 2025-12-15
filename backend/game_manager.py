import uuid
from typing import Dict, Optional
from models import GameState, Player, LinkedInProfile, GameStatus


class GameManager:
    """Manages game state and turn-based logic"""
    
    def __init__(self):
        self.games: Dict[str, GameState] = {}
    
    def create_game(self, player1_profile: LinkedInProfile, player2_profile: LinkedInProfile) -> str:
        """Create a new game and return game ID"""
        game_id = str(uuid.uuid4())
        
        player1 = Player(
            profile=player1_profile,
            health=100,
            name=player1_profile.name
        )
        
        player2 = Player(
            profile=player2_profile,
            health=100,
            name=player2_profile.name
        )
        
        game_state = GameState(
            game_id=game_id,
            player1=player1,
            player2=player2,
            current_turn=1,
            status=GameStatus.IN_PROGRESS,
            round_number=1
        )
        
        self.games[game_id] = game_state
        return game_id
    
    def get_game(self, game_id: str) -> Optional[GameState]:
        """Get game state by ID"""
        return self.games.get(game_id)
    
    def apply_damage(self, game_id: str, player_number: int, damage: int) -> Optional[GameState]:
        """Apply damage to a player and check win condition"""
        game = self.games.get(game_id)
        if not game:
            return None
        
        if player_number == 1:
            game.player1.health = max(0, game.player1.health - damage)
            if game.player1.health <= 0:
                game.status = GameStatus.FINISHED
                game.winner = 2
        elif player_number == 2:
            game.player2.health = max(0, game.player2.health - damage)
            if game.player2.health <= 0:
                game.status = GameStatus.FINISHED
                game.winner = 1
        
        return game
    
    def next_turn(self, game_id: str) -> Optional[GameState]:
        """Switch to next player's turn"""
        game = self.games.get(game_id)
        if not game:
            return None
        
        if game.current_turn == 1:
            game.current_turn = 2
        else:
            game.current_turn = 1
            game.round_number += 1
        
        return game
    
    def update_last_roast(self, game_id: str, roast: str, damage: Optional[int] = None):
        """Update the last roast and damage in game state"""
        game = self.games.get(game_id)
        if not game:
            return
        
        game.last_roast = roast
        game.last_damage = damage







