import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ask_agent(prompt: str) -> str:
    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error contacting Gemini API: {e}"



