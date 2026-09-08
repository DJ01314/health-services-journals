import os
import sys
import time
from google import genai
from google.genai import types

PROMPT_FILE = "prompt.txt"
OUTPUT_FILE = "content.txt"
MODEL_NAME = "gemini-3.8-flash"

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

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

print(f"Sending query to {MODEL_NAME} without Web Search...")

client = genai.Client(api_key=api_key)
config = types.GenerateContentConfig(temperature=0.1)

generated_text = None
max_retries = 3
backoff_seconds = 12

for attempt in range(1, max_retries + 1):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt_text,
            config=config,
        )

        generated_text = response.text
        if generated_text:
            break

    except Exception as e:
        error_msg = str(e)

        if "429" in error_msg or "too_many_requests" in error_msg.lower():
            if attempt < max_retries:
                print(
                    f"Rate limited. Retrying in {backoff_seconds} seconds... "
                    f"(Attempt {attempt}/{max_retries})"
                )
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
            else:
                print(f"Error: Rate limit exceeded after {max_retries} attempts.")
                sys.exit(1)
        else:
            print(f"Error calling Google AI Studio API: {e}")
            sys.exit(1)

if not generated_text:
    print("Error: Gemini returned an empty response.")
    sys.exit(1)

try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(generated_text)

    print(f"Success: AI response written to '{OUTPUT_FILE}'.")
except Exception as e:
    print(f"Error writing to '{OUTPUT_FILE}': {e}")
    sys.exit(1)
