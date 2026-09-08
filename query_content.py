import os
import sys
from google import genai

PROMPT_FILE = "prompt.txt"
OUTPUT_FILE = "content.txt"
MODEL_NAME = "gemini-2.5-flash"

# 1. Validate API Key environment variable
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

# 2. Read prompt text file
if not os.path.exists(PROMPT_FILE):
    print(f"Error: Prompt file '{PROMPT_FILE}' not found.")
    sys.exit(1)

try:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt_text = f.read().strip()
    
    if not prompt_text:
        print(f"Error: Prompt file '{PROMPT_FILE}' is empty.")
        sys.exit(1)
except Exception as e:
    print(f"Error reading '{PROMPT_FILE}': {e}")
    sys.exit(1)

# 3. Initialize Google GenAI client and run query
print(f"Sending query to {MODEL_NAME}...")
try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_text
    )
    
    generated_text = response.text
    if not generated_text:
        print("Warning: Gemini returned an empty response.")
        sys.exit(1)
        
except Exception as e:
    print(f"Error calling Google AI Studio API: {e}")
    sys.exit(1)

# 4. Overwrite output file (content.txt)
try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(generated_text)
    print(f"Success: AI response overwritten to '{OUTPUT_FILE}'.")
except Exception as e:
    print(f"Error writing to '{OUTPUT_FILE}': {e}")
    sys.exit(1)
