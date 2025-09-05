import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Set the API key globally
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ask_agent(prompt: str) -> str:
    try:
        response = genai.responses.create(
            model="gemini-1.5",
            input=prompt
        )
        # The text content is inside response.output_text
        return response.output_text
    except Exception as e:
        return f"Error contacting Gemini API: {e}"

