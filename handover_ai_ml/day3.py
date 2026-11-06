# Day 3 - HandoverHub AI
# Creating and reading a text file

file_name = "meeting_notes.txt"

# Sample meeting notes
content = """
PROJECT: HandoverHub AI

DONE: Frontend design completed
DONE: Project requirements collected

PENDING: Database connection
PENDING: AI API integration

DECISION: Python will be used for backend
DECISION: Gemini API will be tested

BLOCKER: API integration is not completed
"""

# Step 1: Write content into file

with open(file_name, "w", encoding="utf-8") as file:
    file.write(content)

print("File created successfully!")

# Step 2: Read the file

with open(file_name, "r", encoding="utf-8") as file:
    data = file.read()

print("\n===== FILE CONTENT =====")
print(data)