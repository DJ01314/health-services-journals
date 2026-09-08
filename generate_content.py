import os
import sys
import time
import datetime
from google import genai
from google.genai import types

PROMPT_FILE = "prompt.txt"
OUTPUT_FILE = "content.txt"
MODEL_NAME = "gemini-3.6-flash"

MIN_BRIEF_WORDS = 120

NEWS_QUERIES = [
    "medicaid+mental+health",
    "medicare+mental+health+parity",
    "%22health+policy%22+OR+%22health+services+research%22",
    "%22behavioral+health%22+insurance+coverage",
    "Georgia+Medicaid+OR+%22Pathways+to+Coverage%22",
]

ROTATION = {
    0: [  # Monday - federal policy and regulation
        "https://www.cms.gov/newsroom/press-releases",
        "https://www.hhs.gov/about/news/index.html",
        "https://www.federalregister.gov/agencies/centers-for-medicare-medicaid-services",
        "https://aspe.hhs.gov/reports",
        "https://www.cms.gov/priorities/innovation/models",
    ],
    1: [  # Tuesday - JAMA network and translation
        "https://jamanetwork.com/journals/jama/newonline",
        "https://jamanetwork.com/journals/jama-health-forum/newonline",
        "https://jamanetwork.com/journals/jamapsychiatry/newonline",
        "https://jamanetwork.com/journals/jamanetworkopen/newonline",
        "https://www.tradeoffs.org/",
    ],
    2: [  # Wednesday - policy analysis and the HSR field
        "https://www.healthaffairs.org/content/forefront",
        "https://www.kff.org/news/",
        "https://www.macpac.gov/",
        "https://www.medpac.gov/",
        "https://academyhealth.org/blog",
    ],
    3: [  # Thursday - NEJM and preprints
        "https://www.nejm.org/toc/nejm/current",
        "https://catalyst.nejm.org/",
        "https://www.acpjournals.org/toc/aim/current",
        "https://www.medrxiv.org/collection/health-policy",
        "https://www.nber.org/papers?facet=topics%3AHealth",
    ],
    4: [  # Friday - HSR journals and oversight bodies
        "https://www.healthaffairs.org/toc/hlthaff/current",
        "https://www.milbank.org/quarterly/",
        "https://onlinelibrary.wiley.com/journal/14756773",
        "https://journals.lww.com/lww-medicalcare/pages/currenttoc.aspx",
        "https://www.gao.gov/health-care",
    ],
    5: [  # Saturday - Lancet family and psychiatry
        "https://www.thelancet.com/journals/lancet/onlinefirst",
        "https://www.thelancet.com/journals/lanpsy/onlinefirst",
        "https://www.thelancet.com/journals/lanpub/onlinefirst",
        "https://psychiatryonline.org/toc/ps/current",
        "https://www.nimh.nih.gov/about/director/messages",
    ],
    6: [  # Sunday - Georgia, think tanks, behavioral health data
        "https://dch.georgia.gov/",
        "https://georgiarecorder.com/",
        "https://kffhealthnews.org/",
        "https://www.commonwealthfund.org/publications",
        "https://www.samhsa.gov/data/",
    ],
}


def news_feeds(window):
    base = "https://news.google.com/rss/search"
    tail = "hl=en-US&gl=US&ceid=US:en"
    return [f"{base}?q={q}+when:{window}&{tail}" for q in NEWS_QUERIES]


def build_contents(prompt_text, window, rotating_urls):
    urls = news_feeds(window) + rotating_urls
    listing = "\n".join(urls)
    return f"{prompt_text}\n\nRead these URLs:\n{listing}"


def log_url_status(response):
    candidate = response.candidates[0] if response.candidates else None
    metadata = getattr(candidate, "url_context_metadata", None)
    if not metadata:
        return

    for entry in metadata.url_metadata or []:
        print(
            f"[url] {entry.url_retrieval_status}  {entry.retrieved_url}",
            file=sys.stderr,
        )


def call_model(client, config, contents):
    max_retries = 3
    backoff_seconds = 60

    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config,
            )
        except Exception as error:
            message = str(error)
            rate_limited = "429" in message or "too_many_requests" in message.lower()

            if not rate_limited:
                print(f"Error calling Gemini API: {error}", file=sys.stderr)
                sys.exit(1)

            if attempt == max_retries:
                print(f"Rate limit exceeded after {max_retries} attempts.", file=sys.stderr)
                print(message, file=sys.stderr)
                sys.exit(1)

            print(
                f"Rate limited. Retrying in {backoff_seconds}s "
                f"(attempt {attempt}/{max_retries}).",
                file=sys.stderr,
            )
            time.sleep(backoff_seconds)
            backoff_seconds *= 2


api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is missing.", file=sys.stderr)
    sys.exit(1)

if not os.path.exists(PROMPT_FILE):
    print(f"Error: Prompt file '{PROMPT_FILE}' not found.", file=sys.stderr)
    sys.exit(1)

try:
    with open(PROMPT_FILE, "r", encoding="utf-8") as handle:
        prompt_text = handle.read().strip()
except Exception as error:
    print(f"Error reading '{PROMPT_FILE}': {error}", file=sys.stderr)
    sys.exit(1)

if not prompt_text:
    print(f"Error: Prompt file '{PROMPT_FILE}' is empty.", file=sys.stderr)
    sys.exit(1)

weekday = datetime.date.today().weekday()
rotating_urls = ROTATION[weekday]

client = genai.Client(api_key=api_key)
config = types.GenerateContentConfig(
    tools=[types.Tool(url_context=types.UrlContext())],
    temperature=0.1,
)

print(f"Building brief for {datetime.date.today()} using the day {weekday} source set.", file=sys.stderr)

response = call_model(client, config, build_contents(prompt_text, "1d", rotating_urls))
log_url_status(response)
generated_text = (response.text or "").strip()

if len(generated_text.split()) < MIN_BRIEF_WORDS:
    print("Brief came back thin. Retrying with a 48 hour news window.", file=sys.stderr)
    response = call_model(client, config, build_contents(prompt_text, "2d", rotating_urls))
    log_url_status(response)
    wider_text = (response.text or "").strip()

    if len(wider_text.split()) > len(generated_text.split()):
        generated_text = wider_text

if not generated_text:
    print("Error: Gemini returned an empty response.", file=sys.stderr)
    sys.exit(1)

try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        handle.write(generated_text + "\n")
except Exception as error:
    print(f"Error writing to '{OUTPUT_FILE}': {error}", file=sys.stderr)
    sys.exit(1)

print(f"Success: brief written to '{OUTPUT_FILE}'.", file=sys.stderr)
