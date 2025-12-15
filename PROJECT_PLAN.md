# Project Plan

## Goal
Document the gameplay flow, required AI interactions, and UI expectations for the LinkedIn Roast Battle Game so frontend and backend stay aligned.

## Gameplay Flow
- **Intro**: Collect both players’ names and LinkedIn profile URLs (other profile fields optional).
- **Battle**: Streetfighter-style view showing both avatars, most recent roasts, and live health bars.
- **End**: Display winner with final health and call-to-action to restart.

## AI Model Usage (3 calls per turn cycle)
- **P1 Roast Generation**: Create a roast targeting Player 2 based on weaknesses in Player 2’s LinkedIn profile (authored by Player 1).
- **P2 Roast Generation**: Create a roast targeting Player 1 based on weaknesses in Player 1’s LinkedIn profile (authored by Player 2).
- **Roast Judge**: Evaluate a submitted roast for effectiveness and return damage scoring plus short reasoning.

## Frontend Screen Expectations
- **Setup Screen**: Form for both players (name required, LinkedIn link optional). Button starts game and hits backend start endpoint.
- **Battle Screen**: Two-column “versus” layout with avatars/placeholders, latest roast text bubbles, turn indicator, action buttons (Generate Roast, Review & Deal Damage), and health bars synced to game state.
- **End Screen**: Winner announcement, final roasts summary snippet, and “Play Again” button returning to setup.

## Data/Integration Notes
- Frontend should persist the active game ID and current turn, and fetch updated game state after judge calls.
- Health values and roasts should be pulled from backend responses to avoid client drift.
- Keep UI Tailwind-friendly with responsive layout; dark/light neutral palette.

