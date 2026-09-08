import os
import sys
import time
from google import genai
from google.genai import types

PROMPT_FILE = "prompt.txt"
OUTPUT_FILE = "content.txt"
MODEL_NAME = "gemini-3.6-flash"

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

if not os.path.exists(PROMPT_FILE):
    print(f"Error: Prompt file '{PROMPT_FILE}' not found.")
    sys.exit(1)

try:
    with open(PROMPT_FILE, "r", encoding="utf-8") as file:
        prompt_text = file.read().strip()

    if not prompt_text:
        print(f"Error: Prompt file '{PROMPT_FILE}' is empty.")
        sys.exit(1)
except Exception as error:
    print(f"Error reading '{PROMPT_FILE}': {error}")
    sys.exit(1)

search_instruction = """
Use no more than two web search queries total.
Do not perform follow-up searches.
If reliable information cannot be found within two searches, omit it.
"""

prompt_text = f"{search_instruction}\n\n{prompt_text}"

print(f"Sending query to {MODEL_NAME} with Web Search enabled...")

client = genai.Client(api_key=api_key)

config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.1,
)

generated_text = None
max_retries = 3
backoff_seconds = 60

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

    except Exception as error:
        error_message = str(error)

        if (
            "429" in error_message
            or "too_many_requests" in error_message.lower()
        ):
            if attempt < max_retries:
                print(
                    f"Rate limited. Retrying in {backoff_seconds} seconds... "
                    f"(Attempt {attempt}/{max_retries})"
                )
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
            else:
                print(f"Error: Rate limit exceeded after {max_retries} attempts.")
                print(error_message)
                sys.exit(1)
        else:
            print(f"Error calling Google AI Studio API: {error}")
            sys.exit(1)

if not generated_text:
    print("Error: Gemini returned an empty response.")
    sys.exit(1)

try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(generated_text)

    print(f"Success: AI response written to '{OUTPUT_FILE}'.")
except Exception as error:
    print(f"Error writing to '{OUTPUT_FILE}': {error}")
    sys.exit(1)
