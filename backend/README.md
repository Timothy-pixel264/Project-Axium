# LinkedIn Roast Battle - Backend

FastAPI backend for the LinkedIn Roast Battle game.

## Setup

### Using uv (Recommended)

1. Install dependencies:
```bash
uv sync
```

2. Run the server:
```bash
uv run python main.py
```

Or with uvicorn directly:
```bash
uv run uvicorn main:app --reload --port 8000
```

### Using pip (Alternative)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `POST /api/game/start` - Start a new game
- `GET /api/game/{game_id}` - Get game state
- `POST /api/game/{game_id}/roast` - Generate a roast
- `POST /api/game/{game_id}/review` - Review a roast and calculate damage

## Model Loading

The Qwen2.5-3B-Instruct model will be downloaded automatically on first run. This may take some time and requires ~6GB of disk space. If the model fails to load, the service will use mock responses for development.

