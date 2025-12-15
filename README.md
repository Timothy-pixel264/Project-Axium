# LinkedIn Roast Battle Game

A turn-based battle game where two players input LinkedIn profiles, AI generates roasts, and another AI reviews them to determine damage in a battle-to-the-death format.

## Features

- Turn-based battle system with three UI stages (Setup, Battle, Victory)
- AI-powered roast generation using Qwen2.5-3B-Instruct
- AI-powered roast review and damage calculation (judge call)
- Real-time health tracking with Streetfighter-style battle view
- Beautiful, modern UI with Tailwind CSS

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: React with TypeScript
- **AI Model**: Qwen/Qwen2.5-3B-Instruct (via Hugging Face Transformers)
- **Styling**: Tailwind CSS

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

**Note**: On first run, the Qwen2.5-3B-Instruct model will be downloaded automatically (~6GB). This may take some time. If the model fails to load, the service will use mock responses for development.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## How to Play

1. **Setup Screen**: Enter both players’ names (required) and LinkedIn links (optional). Start creates a game.
2. **Battle Screen** (Streetfighter-style): 
   - Current player clicks **Generate Roast** (AI generates roast vs. opponent).
   - Then click **Review Roast & Deal Damage** (AI judge scores roast and returns damage).
   - Health bars update from backend; turns alternate automatically.
3. **End Screen**: Shows the winner, final health, and option to play again.

## AI Model Usage (per turn)
- **Player 1 Roast Generation**: Create roast targeting Player 2.
- **Player 2 Roast Generation**: Create roast targeting Player 1.
- **Roast Judge**: Score the roast and return damage + brief rationale.

## Project Structure

```
Project-Axium/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ai_service.py        # AI model integration
│   ├── game_manager.py      # Game state management
│   ├── models.py            # Pydantic models
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main app component
│   │   ├── components/      # React components
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript types
│   └── package.json         # Node dependencies
└── README.md
```

## API Endpoints

- `POST /api/game/start` - Start a new game with two profiles
- `GET /api/game/{game_id}` - Get current game state
- `POST /api/game/{game_id}/roast` - Generate a roast for current player
- `POST /api/game/{game_id}/review` - Review a roast and calculate damage

## Development Notes

- The game state is stored in-memory (will be lost on server restart)
- For production, consider adding a database (Redis/PostgreSQL) for persistent game state
- The AI model can be run locally or via Hugging Face Inference API
- CORS is configured to allow requests from the React dev server

## Frontend Screens (Next.js + Tailwind)
- **Setup**: Dual player form (name + LinkedIn URL) and start button.
- **Battle**: Two-column avatars, latest roasts, turn indicator, action buttons (Generate, Review/Deal Damage), and health bars bound to backend state.
- **End**: Winner banner, quick recap, and Play Again to restart at setup.

## License

MIT







