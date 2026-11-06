# HandoverHub AI - Day 2

# Project information using Dictionary

project = {
    "name": "HandoverHub AI",
    "status": "In Progress",
    "leader": "Rajveer"
}

# Project tasks using List

tasks = [
    {
        "task": "Create Frontend",
        "status": "Completed"
    },
    {
        "task": "Create Database",
        "status": "Pending"
    },
    {
        "task": "Integrate AI API",
        "status": "Pending"
    },
    {
        "task": "Test Application",
        "status": "Completed"
    }
]

# Display project information

print("===== PROJECT INFORMATION =====")

print("Project Name:", project["name"])
print("Project Status:", project["status"])
print("Project Leader:", project["leader"])

# Display all tasks

print("\n===== TASK REPORT =====")

for item in tasks:

    print("Task:", item["task"])
    print("Status:", item["status"])
    print("--------------------")

# Count completed and pending tasks

completed = 0
pending = 0

for item in tasks:

    if item["status"] == "Completed":
        completed += 1

    else:
        pending += 1

print("Completed Tasks:", completed)
print("Pending Tasks:", pending)
print("Total Tasks:", len(tasks))