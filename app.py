import streamlit as st
import anthropic
from dotenv import load_dotenv
import os
from icalendar import Calendar, Event
from datetime import datetime
import json
import pdfplumber
import tempfile

# Load API key
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

st.title("Syllabus Scraper")
st.write("Upload your syllabus PDF and we'll extract all your deadlines into a calendar file!")

uploaded_file = st.file_uploader("Upload your syllabus PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Extract Deadlines"):
        with st.spinner("Reading your syllabus..."):
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Read the PDF
            syllabus_text = ""
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    syllabus_text += page.extract_text()

        with st.spinner("Extracting deadlines with AI..."):
            # Ask Claude to extract deadlines
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extract all deadlines from this syllabus and return them as a JSON array.
Each item should have 'name' and 'date' fields.
Date format should be YYYY-MM-DD.
Return only the JSON array, nothing else.

{syllabus_text}"""
                    }
                ]
            )

            # Parse response
            response_text = message.content[0].text
            response_text = response_text.strip()
            response_text = response_text.removeprefix("```json").removeprefix("```").removesuffix("```")
            response_text = response_text.strip()
            deadlines = json.loads(response_text)

        # Show deadlines to user
        st.success(f"Found {len(deadlines)} deadlines!")
        st.subheader("Your Deadlines:")
        for deadline in deadlines:
            st.write(f"📅 **{deadline['name']}** — {deadline['date']}")

        # Build calendar
        cal = Calendar()
        cal.add('prodid', '-//Syllabus Scraper//EN')
        cal.add('version', '2.0')

        for deadline in deadlines:
            event = Event()
            event.add('summary', deadline['name'])
            event.add('dtstart', datetime.strptime(deadline['date'], '%Y-%m-%d').date())
            event.add('dtend', datetime.strptime(deadline['date'], '%Y-%m-%d').date())
            cal.add_component(event)

        # Download button
        st.download_button(
            label="Download Calendar File",
            data=cal.to_ical(),
            file_name="syllabus.ics",
            mime="text/calendar"
        )

        # Cleanup temp file
        os.unlink(tmp_path)