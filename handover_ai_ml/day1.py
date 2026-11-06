# HandoverHub AI - Project Report

def project_report(name, completed, pending):

    total = completed + pending

    print("===== PROJECT REPORT =====")

    print("Project Name:", name)
    print("Completed Tasks:", completed)
    print("Pending Tasks:", pending)
    print("Total Tasks:", total)

    return total


# Calling the function

result = project_report(
    "HandoverHub AI",
    5,
    3
)

print("Report Generated Successfully!")