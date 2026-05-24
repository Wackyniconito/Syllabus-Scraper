import streamlit as st
import anthropic
from dotenv import load_dotenv
import os
from icalendar import Calendar, Event
import json
import pdfplumber
import tempfile
from datetime import datetime, timedelta

# Load API key
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

st.title("Syllabus Scraper")
st.write("Upload your syllabus PDF and we'll extract all your deadlines into a calendar file!")
 
# Pick Calendar
st.write("Pick your calendar!")

st.button("Google Calendar", key="Google")
st.session_state['calendar_choice'] = "Google"

if 'calendar_choice' not in st.session_state:
    st.session_state['calendar_choice'] = None


# File Upload
if uploaded_file is not None:
    if st.button("Extract Deadlines"):
        with st.spinner("Reading syllabus..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            syllabus_text = ""
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    syllabus_text += page.extract_text()

        with st.spinner("Making life easier with Artificial Intelligence..."):
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extract all deadlines from this syllabus and return them as a JSON array.
Each item should have 'name' and 'date' fields.
Date format should be Month Day, Year.
Return only the JSON array, nothing else.

{syllabus_text}"""
                    }
                ]
            )

            response_text = message.content[0].text
            response_text = response_text.strip()
            response_text = response_text.removeprefix("```json").removeprefix("```").removesuffix("```")
            response_text = response_text.strip()
            deadlines = json.loads(response_text)

        # Show deadlines to user
        st.success(f"Found {len(deadlines)} deadlines!")
        st.subheader("Your Deadlines:")

        for deadline in deadlines:
            date_obj = datetime.strptime(deadline['date'], '%B %d, %Y')
            google_date = date_obj.strftime('%B %d, %Y')
            next_day = (date_obj + timedelta(days=1)).strftime('%B %d, %Y')
            
            google_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={deadline['name'].replace(' ', '+')}&dates={google_date}/{next_day}"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📅 **{deadline['name']}** — {deadline['date']}")
            with col2:
                st.link_button("Add to Google", google_link)

        # Build calendar
        cal = Calendar()
        cal.add('prodid', '-//Syllabus Scraper//EN')
        cal.add('version', '2.0')

        for deadline in deadlines:
            event = Event()
            event.add('summary', deadline['name'])
            event.add('dtstart', datetime.strptime(deadline['date'], '%B %d, %Y').date())
            event.add('dtend', datetime.strptime(deadline['date'], '%B %d, %Y').date())
            cal.add_component(event)

        # Download button
        st.divider()
        st.subheader("Add All Deadlines to Your Calendar")
        st.write("Click the button below to download all your deadlines at once. Then just double click the downloaded file and your default calendar app will import everything automatically!")

        st.download_button(
            label="⬇️ Add ALL Deadlines to Calendar at Once",
            data=cal.to_ical(),
            file_name="syllabus.ics",
            mime="text/calendar"
        )

        st.caption("✅ Works with Outlook, Google Calendar, and Apple Calendar")

        st.info("After downloading, click below to open Google Calendar & import your file!")
    

            # Cleanup temp file
        os.unlink(tmp_path)