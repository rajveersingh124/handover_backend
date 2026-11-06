# HandoverHub AI - Basic Information Extraction

file_name = "meeting_notes.txt"

# Categories to store information

handover_data = {
    "completed": [],
    "pending": [],
    "decisions": [],
    "blockers": []
}

# Connect text labels with categories

category_map = {
    "DONE": "completed",
    "PENDING": "pending",
    "DECISION": "decisions",
    "BLOCKER": "blockers"
}

# Read the meeting notes file

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
                    "source": file_name,
                    "line": line_number,
                    "text": message.strip()
                })

    # Display extracted information

    print("===== HANDOVER REPORT =====")

    for category, records in handover_data.items():

        print("\n", category.upper())

        for record in records:

            print("-", record["text"])

            print(
                "  Source:",
                record["source"],
                "| Line:",
                record["line"]
            )

except FileNotFoundError:

    print("Error: Meeting notes file not found!")