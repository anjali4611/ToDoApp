import re
import datetime
import spacy
from dateparser.search import search_dates
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# Load credentials for Google Calendar API
creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/calendar"])
service = build("calendar", "v3", credentials=creds)

def extract_info(user_input):
    doc = nlp(user_input)

    # Extract email
    email_match = re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", user_input)
    email = email_match.group(0) if email_match else None

    # Extract title after "about"
    title = "Meeting"
    for token in doc:
        if token.text.lower() == "about" and token.i + 1 < len(doc):
            title = doc[token.i + 1:].text.strip().rstrip('.')
            break

    # Extract date/time using dateparser
    date = None
    start_time = None
    end_time = None

    dt_matches = list(search_dates(user_input))

    if len(dt_matches) >= 2:
        start = dt_matches[0][1]
        end = dt_matches[1][1]
        date = start.date()
        start_time = start.strftime("%H:%M")
        end_time = end.strftime("%H:%M")
    elif len(dt_matches) == 1:
        start = dt_matches[0][1]
        date = start.date()
        start_time = start.strftime("%H:%M")
        end = start + datetime.timedelta(hours=1)
        end_time = end.strftime("%H:%M")

    return title, str(date), start_time, end_time, email

def create_event_nlp():
    user_input = input("🗣 Describe your meeting (e.g. 'Schedule a meeting with xyz@gmail.com on July 14 from 5:30 PM to 6:30 PM about Python class'):\n> ")
    title, date, start_time, end_time, email = extract_info(user_input)

    if not (date and start_time and end_time):
        print("❗ Could not extract date/time properly. Please try again with more details.")
        return

    start_datetime = f"{date}T{start_time}:00"
    end_datetime = f"{date}T{end_time}:00"

    event = {
        "summary": title,
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
    }

    if email:
        event["attendees"] = [{"email": email}]

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Event created: {created_event['htmlLink']}")

def list_events():
    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary", timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
        return

    for idx, event in enumerate(events, start=1):
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(f"{idx}. {event['summary']} at {start} (ID: {event['id']})")

def delete_event():
    list_events()
    event_id = input("Enter the event ID to delete: ").strip()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    print("❌ Event deleted.")

def main():
    while True:
        print("\nWhat would you like to do?")
        print("1. 🗓 Schedule meeting ")
        print("2. 📋 View upcoming meetings")
        print("3. ❌ Cancel a meeting")
        print("4. 🚪 Exit")

        choice = input("Choose (1/2/3/4): ").strip()

        if choice == "1":
            create_event_nlp()
        elif choice == "2":
            list_events()
        elif choice == "3":
            delete_event()
        elif choice == "4":
            break
        else:
            print("❗ Invalid choice, try again.")

if __name__ == "__main__":
    main()
