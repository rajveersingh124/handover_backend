# HandoverHub AI - Day 4
# JSON + Exception Handling

import json
import os

file_name = "meeting_notes.txt"
report_file = "handover_report.json"

# Step 1: Create sample file if it does not exist

if not os.path.exists(file_name):

    sample_content = """
PROJECT: HandoverHub AI
DONE: Frontend completed
DONE: Requirements collected
PENDING: Database connection
PENDING: AI API integration
DECISION: Python will be used for backend
BLOCKER: API integration is pending
"""

    with open(file_name, "w", encoding="utf-8") as file:
        file.write(sample_content)


# Step 2: Create report dictionary

handover_data = {
    "project_name": "HandoverHub AI",
    "completed": [],
    "pending": [],
    "decisions": [],
    "blockers": []
}

category_map = {
    "DONE": "completed",
    "PENDING": "pending",
    "DECISION": "decisions",
    "BLOCKER": "blockers"
}


# Step 3: Read and process meeting notes

try:

    with open(file_name, "r", encoding="utf-8") as file:

        for line_number, line in enumerate(file, start=1):

            clean_line = line.strip()

            if ":" not in clean_line:
                continue

            prefix, message = clean_line.split(":", 1)

            category = category_map.get(prefix.strip())

            if category:

                handover_data[category].append({
                    "text": message.strip(),
                    "source": file_name,
                    "line": line_number
                })


# Handle file errors

except FileNotFoundError:

    print("Error: Meeting notes file not found!")

    raise SystemExit

except OSError as error:

    print("File Error:", error)

    raise SystemExit


# Step 4: Save data into JSON file

try:

    with open(report_file, "w", encoding="utf-8") as file:

        json.dump(
            handover_data,
            file,
            indent=4
        )

    print("JSON report created successfully!")


except OSError as error:

    print("Unable to save report:", error)

    raise SystemExit


# Step 5: Read JSON file

try:

    with open(report_file, "r", encoding="utf-8") as file:

        final_report = json.load(file)

    print("\n===== HANDOVER REPORT =====")

    print("Project:", final_report["project_name"])

    for category in [
        "completed",
        "pending",
        "decisions",
        "blockers"
    ]:

        print("\n" + category.upper())

        for item in final_report[category]:

            print("-", item["text"])

            print(
                "  Source:",
                item["source"],
                "| Line:",
                item["line"]
            )


except FileNotFoundError:

    print("JSON report file not found!")

except json.JSONDecodeError:

    print("Error: JSON file contains invalid data!")

except OSError as error:

    print("Unable to read report:", error)