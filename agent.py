import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_agent(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # fast, cheap model
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error contacting Gemini API: {e}"
