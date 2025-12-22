from google import genai
import os
def gemini_generate_plan(prompt):
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return None

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    return response.text
