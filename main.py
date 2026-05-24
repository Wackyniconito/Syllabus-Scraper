import anthropic
from dotenv import load_dotenv
import os
from icalendar import Calendar, Event
from datetime import datetime
import json
import pdfplumber

# Load your API key from .env file
load_dotenv()

# Connect to Claude
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Find all PDFs in the current folder

pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]

if len(pdf_files) ==0:
    print("No PDF files found! Please add your syllabus PDF to this folder.")
    exit()

# Show the user their options
print("Syllabus PDFs found!")
for i, pdf in enumerate(pdf_files):
    print(f"    {i + 1}. {pdf}")

# Let them pick one
choice = int(input("\nEnter the number of your syllabus: ")) - 1
pdf_path = pdf_files[choice]

# Read the PDF
syllabus_text = ""
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        syllabus_text += page.extract_text()

print(f"Successfully read the PDF!")
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": f"""Extract all deadlines from this syllabus and return them as a JSON array.
Each item should have 'name' and 'date' fields.
Date format should be MM DD, YY.
Return only the JSON array, nothing else.

{syllabus_text}"""
        }
    ]
)

# Parse Claude's response
response_text = message.content[0].text
response_text = response_text.strip()
response_text = response_text.removeprefix("```json").removeprefix("```").removesuffix("```")
response_text = response_text.strip()
deadlines = json.loads(response_text)
print("Deadlines found:")
for deadline in deadlines:
    print(f"  - {deadline['name']}: {deadline['date']}")

# Create the calendar
cal = Calendar()
cal.add('prodid', '-//Syllabus Scraper//EN')
cal.add('version', '2.0')

# Add each deadline as a calendar event
for deadline in deadlines:
    event = Event()
    event.add('summary', deadline['name'])
    event.add('dtstart', datetime.strptime(deadline['date'], '%B %d, %Y').date())
    event.add('dtend', datetime.strptime(deadline['date'], '%B %d, %Y').date())
    cal.add_component(event)

# Save the .ics file
with open('syllabus.ics', 'wb') as f:
    f.write(cal.to_ical())

print("\nSuccess! syllabus.ics has been created.")
print("Double click it to import into your calendar!")  