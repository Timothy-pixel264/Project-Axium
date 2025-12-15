import json
import re
from typing import Dict
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from models import LinkedInProfile


class AIService:
    """AI service for generating roasts and reviewing them using Qwen2.5-3B-Instruct"""
    
    def __init__(self):
        self.model_name = "Qwen/Qwen2.5-3B-Instruct"
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Qwen model and tokenizer"""
        try:
            print(f"Loading model {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to mock responses for development")
            self.model = None
            self.tokenizer = None
    
    def _generate_text(self, prompt: str, max_length: int = 512) -> str:
        """Generate text using the model"""
        if self.model is None or self.tokenizer is None:
            # Mock response for development/testing
            return self._mock_response(prompt)
        
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            
            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return response.strip()
        except Exception as e:
            print(f"Error generating text: {e}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Mock response when model is not available"""
        if "roast" in prompt.lower() and "review" not in prompt.lower():
            return "Your LinkedIn profile screams 'I put 'synergy' in my bio unironically.'"
        elif "review" in prompt.lower() or "damage" in prompt.lower():
            return '{"damage": 45, "reasoning": "Moderately witty but could be sharper"}'
        return "Mock response"
    
    def generate_roast(self, attacker_profile: LinkedInProfile, target_profile: LinkedInProfile) -> str:
        """Generate a roast based on target profile"""
        profile_summary = f"""
Name: {target_profile.name}
Headline: {target_profile.headline or 'N/A'}
Bio: {target_profile.bio or 'N/A'}
Experience: {', '.join(target_profile.experience) if target_profile.experience else 'N/A'}
Skills: {', '.join(target_profile.skills) if target_profile.skills else 'N/A'}
Education: {', '.join(target_profile.education) if target_profile.education else 'N/A'}
"""
        
        prompt = f"""Generate a creative, witty roast based on this LinkedIn profile. Make it funny but not offensive. Focus on their job title, experience, skills, or bio. Keep it concise (1-2 sentences).

LinkedIn Profile:
{profile_summary}

Roast:"""
        
        roast = self._generate_text(prompt, max_length=200)
        return roast.strip()
    
    def review_roast(self, roast: str, target_profile: LinkedInProfile) -> Dict[str, any]:
        """Review a roast and calculate damage (0-100)"""
        profile_summary = f"""
Name: {target_profile.name}
Headline: {target_profile.headline or 'N/A'}
Bio: {target_profile.bio or 'N/A'}
"""
        
        prompt = f"""Rate this roast on a scale of 0-100 for effectiveness, creativity, and humor. Consider: wit, relevance to profile, comedic value.

Target Profile:
{profile_summary}

Roast: {roast}

Return ONLY a valid JSON object with this exact format:
{{"damage": <number 0-100>, "reasoning": "<brief explanation>"}}

JSON:"""
        
        response = self._generate_text(prompt, max_length=300)
        
        # Try to extract JSON from response
        try:
            # Look for JSON object in the response
            json_match = re.search(r'\{[^{}]*"damage"[^{}]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Try parsing the whole response
                result = json.loads(response)
            
            damage = int(result.get("damage", 50))
            reasoning = result.get("reasoning", "Standard roast")
            
            # Ensure damage is in valid range
            damage = max(0, min(100, damage))
            
            return {
                "damage": damage,
                "reasoning": reasoning
            }
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error parsing review response: {e}")
            print(f"Response was: {response}")
            # Fallback: estimate damage based on roast length and keywords
            damage = min(100, len(roast) // 2)
            return {
                "damage": damage,
                "reasoning": "Could not parse AI response, using fallback calculation"
            }




