"""
morning-briefing: gathers weather + today's calendar + news headlines,
asks Claude to write a short briefing from them, and emails it to yourself via Gmail.

This isn't a "loop" agent like example-agent (no back-and-forth tool use at
runtime) — it's the other common agent shape: gather context from a few
sources, hand it to the model once to synthesize, then take one real-world
action (send an email) with the result. Same underlying idea: LLM + tools,
just tools called by you up front instead of requested by the model mid-conversation.

Setup: see README.md for the Google Cloud / OAuth steps. First run opens a
browser to authorize; after that it's fully silent (safe for cron).
"""

import base64
import os
import datetime
from email.mime.text import MIMEText

import requests
import feedparser
from anthropic import Anthropic

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
]

# Configure these for your location / preferences.
LATITUDE = float(os.environ.get("BRIEFING_LAT", "34.05"))   # default: Los Angeles
LONGITUDE = float(os.environ.get("BRIEFING_LON", "-118.24"))
TO_EMAIL = os.environ["BRIEFING_TO_EMAIL"]  # where the briefing gets sent
NEWS_FEED_URL = os.environ.get("BRIEFING_NEWS_FEED", "https://feeds.bbci.co.uk/news/rss.xml")

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(HERE, "token.json")
CREDENTIALS_PATH = os.path.join(HERE, "credentials.json")

anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"


# --- Auth ----------------------------------------------------------------

def get_google_credentials() -> Credentials:
    """Load saved OAuth token, refreshing or running the browser flow if needed."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


# --- Gather context --------------------------------------------------------

def get_weather() -> str:
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "temperature_unit": "fahrenheit",
            "timezone": "auto",
        },
        timeout=10,
    )
    data = resp.json()
    current = data["current"]
    today_high = data["daily"]["temperature_2m_max"][0]
    today_low = data["daily"]["temperature_2m_min"][0]
    return (
        f"Currently {current['temperature_2m']}°F. "
        f"Today's range: {today_low}°F to {today_high}°F."
    )


def get_calendar_events(creds: Credentials) -> str:
    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.now(datetime.timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1)

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        return "No events on the calendar today."

    lines = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        lines.append(f"- {start}: {event.get('summary', '(no title)')}")
    return "\n".join(lines)


def get_news_headlines(limit: int = 5) -> str:
    feed = feedparser.parse(NEWS_FEED_URL)
    headlines = [entry.title for entry in feed.entries[:limit]]
    return "\n".join(f"- {h}" for h in headlines)


# --- Synthesize with Claude --------------------------------------------------

def write_briefing(weather: str, calendar: str, news: str) -> str:
    prompt = f"""Write a short, friendly morning briefing email using this info.
Keep it under 200 words, plain text (no markdown headers), and end with a
one-line "have a good day" style sign-off.

WEATHER:
{weather}

CALENDAR TODAY:
{calendar}

NEWS HEADLINES:
{news}
"""
    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


# --- Send --------------------------------------------------------------------

def send_email(creds: Credentials, body: str) -> None:
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = TO_EMAIL
    message["subject"] = f"Morning Briefing — {datetime.date.today().strftime('%A, %B %d')}"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(userId="me", body={"raw": raw}).execute()


# --- Main ----------------------------------------------------------------

def main():
    creds = get_google_credentials()

    weather = get_weather()
    calendar = get_calendar_events(creds)
    news = get_news_headlines()

    briefing = write_briefing(weather, calendar, news)
    send_email(creds, briefing)

    print("Sent briefing:\n")
    print(briefing)


if __name__ == "__main__":
    main()
