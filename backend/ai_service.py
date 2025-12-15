import json
import os
import re
from typing import Dict

import requests
from dotenv import load_dotenv
from models import LinkedInProfile


ROAST_SYSTEM_PROMPT = (
    "You are an AI roast generator in a turn-based LinkedIn roast battle game. "
    "You receive noisy, web‑scraped LinkedIn profile content as context. "
    "Write short, witty, non‑hateful roasts that target weaknesses, fluff, or buzzwords "
    "in the target's LinkedIn presence. Keep outputs safe for a PG‑13 audience."
)

JUDGE_SYSTEM_PROMPT = (
    "You are an impartial judge in a LinkedIn roast battle game. "
    "Given a roast and the target's (possibly noisy) web‑scraped LinkedIn content, "
    "return ONLY JSON with a damage score from 0‑100 and a one‑sentence explanation, "
    "evaluating wit, relevance to the profile, and comedic impact."
)


class AIService:
    """AI service for generating roasts and reviewing them using Hugging Face Inference API."""

    def __init__(self):
        # Ensure backend/.env is loaded so HUGGING_FACE_API is available even when using uv
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(backend_dir, ".env")
        load_dotenv(dotenv_path=env_path, override=False)

        self.model_name = "Qwen/Qwen2.5-3B-Instruct"
        self.api_token = os.getenv("HUGGING_FACE_API")
        self.api_url = os.getenv(
            "HUGGING_FACE_API_URL",
            f"https://api-inference.huggingface.co/models/{self.model_name}",
        )

    def _call_hf(self, prompt: str, max_new_tokens: int = 256) -> str:
        """Call Hugging Face Inference API or raise an error if invocation fails."""
        if not self.api_token:
            raise RuntimeError(
                "HUGGING_FACE_API environment variable is not set; cannot call Hugging Face API."
            )

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False,
            },
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # HF text generation endpoints typically return a list of {generated_text: "..."}
            if isinstance(data, list) and data and isinstance(data[0], dict):
                text = data[0].get("generated_text")
                if isinstance(text, str):
                    return text.strip()

            # Some endpoints may return a dict with choices or generated_text
            if isinstance(data, dict):
                if "generated_text" in data and isinstance(data["generated_text"], str):
                    return data["generated_text"].strip()
                choices = data.get("choices")
                if isinstance(choices, list) and choices:
                    first = choices[0]
                    if isinstance(first, dict) and isinstance(first.get("text"), str):
                        return first["text"].strip()

            raise RuntimeError(f"Unexpected Hugging Face response format: {data}")
        except Exception as e:
            # Bubble up so FastAPI can return a 500 to the client
            raise RuntimeError(f"Hugging Face API error: {e}") from e

    def generate_roast(self, attacker_profile: LinkedInProfile, target_profile: LinkedInProfile) -> str:
        """Generate a roast targeting weaknesses in the opponent's LinkedIn profile.

        The context is assumed to come from web‑scraped LinkedIn profile content
        that has already been processed into structured fields.
        """
        profile_summary = f"""
Name: {target_profile.name}
Headline: {target_profile.headline or 'N/A'}
Summary_or_WebScrape: {target_profile.bio or 'N/A'}
Experience_snippets: {', '.join(target_profile.experience) if target_profile.experience else 'N/A'}
Skills_snippets: {', '.join(target_profile.skills) if target_profile.skills else 'N/A'}
Education_snippets: {', '.join(target_profile.education) if target_profile.education else 'N/A'}
"""

        prompt = f"""{ROAST_SYSTEM_PROMPT}

CONTEXT (web‑scraped LinkedIn profile):
{profile_summary}

INSTRUCTION:
- Write a single roast (1–2 sentences).
- Make it witty and targeted to the profile's weaknesses or cringe.
- Do NOT include JSON or explanations, only the roast line(s).

Roast:"""

        roast = self._call_hf(prompt, max_new_tokens=200)
        return roast.strip()

    def review_roast(self, roast: str, target_profile: LinkedInProfile) -> Dict[str, any]:
        """Review a roast and calculate damage (0-100) using the LLM only.

        If the LLM call or JSON parsing fails, this will raise an error so the
        client gets a clear 500 instead of a mocked result.
        """
        profile_summary = f"""
Name: {target_profile.name}
Headline: {target_profile.headline or 'N/A'}
Summary_or_WebScrape: {target_profile.bio or 'N/A'}
"""

        prompt = f"""{JUDGE_SYSTEM_PROMPT}

CONTEXT (web‑scraped LinkedIn profile):
{profile_summary}

ROAST:
{roast}

INSTRUCTION:
- Respond with ONLY a JSON object.
- Format: {{"damage": <integer 0-100>, "reasoning": "<brief explanation>"}}
- Do not include any extra text before or after the JSON.

JSON:"""

        response = self._call_hf(prompt, max_new_tokens=300)

        # Try to extract JSON from response; on failure, raise instead of mocking.
        try:
            json_match = re.search(r"\{[^{}]*\"damage\"[^{}]*\}", response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)

            damage = int(result.get("damage", 50))
            reasoning = result.get("reasoning", "Standard roast")

            damage = max(0, min(100, damage))

            return {
                "damage": damage,
                "reasoning": reasoning,
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Surface a clear error; FastAPI layer will turn this into 500.
            raise RuntimeError(
                f"Failed to parse LLM review response as JSON: {e}; raw response: {response}"
            ) from e




