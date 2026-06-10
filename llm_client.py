import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class AgentBrain:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Using llama-3.3-70b-versatile as it's highly stable
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30.0)
            
            # Print the error body if it fails so we can see exactly what Groq is complaining about
            if response.status_code != 200:
                print(f"Error Body: {response.text}")
                response.raise_for_status()
                
            data = response.json()
            return data["choices"][0]["message"]["content"]
