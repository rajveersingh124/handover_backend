# HandoverHub AI - Day 7
# Smart Handover Brief + Human Review Gate
# This script uses the Day 6 JSON report. It does not call the AI API.

import json
import re
from pathlib import Path


# --------------------------------------------------
# 1. FILE SETTINGS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
REPORT_FILE = BASE_DIR / "handover_ai_report.json"
SOURCE_FILE = BASE_DIR / "meeting_notes.txt"
BRIEF_FILE = BASE_DIR / "incoming_member_brief.md"
REVIEW_FILE = BASE_DIR / "handover_review_checklist.json"

EVIDENCE_CATEGORIES = [
    "completed",
    "pending",
    "decisions",
    "blockers",
    "risks",
    "dependencies",
    "next_actions",
    "ownership_gaps",
    "conflicts",
]


# --------------------------------------------------
# 2. SAFE HELPERS
# --------------------------------------------------

def read_json(path):
    """Read a JSON file and return its contents."""
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def safe_list(value):
    """Return a list; use an empty list for missing or invalid values."""
    return value if isinstance(value, list) else []


def clean_text(value, fallback="Not provided"):
    """Convert a value into readable text without displaying Python None."""
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).strip()


def redact_sensitive_text(value):
    """Mask common secret-like values before putting evidence in the brief."""
    text = str(value)
    patterns = [
        (r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
        (r"(?i)(password\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
        (r"(?i)(secret\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
        (r"(?i)(access[_ -]?token\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
        (r"(?i)Bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def load_source_lines(path):
    """Load original source lines using one-based line numbers."""
    with path.open("r", encoding="utf-8-sig") as file:
        lines = file.readlines()
    return {
        number: line.rstrip("\r\n")
        for number, line in enumerate(lines, start=1)
    }


def verify_evidence(source_line, evidence, line_map):
    """Independently confirm a cited source line against the original notes."""
    if isinstance(source_line, bool):
        return False

    try:
        number = int(source_line)
    except (TypeError, ValueError):
        return False

    if number not in line_map or not isinstance(evidence, str):
        return False

    return evidence.strip() == line_map[number].strip()


def verify_item(item, category, line_map):
    """Verify the main evidence and both sides of a conflict when present."""
    if not isinstance(item, dict):
        return {"source_check": "NEEDS VERIFICATION"}

    primary_ok = verify_evidence(
        item.get("source_line"), item.get("evidence"), line_map
    )

    result = {
        "source_check": "MATCHED" if primary_ok else "NEEDS VERIFICATION"
    }

    if category == "conflicts":
        related_ok = verify_evidence(
            item.get("related_source_line"),
            item.get("related_evidence"),
            line_map,
        )
        result["related_source_check"] = (
            "MATCHED" if related_ok else "NEEDS VERIFICATION"
        )
        if not related_ok:
            result["source_check"] = "NEEDS VERIFICATION"

    return result


def format_evidence(item, line_map, category):
    """Return a readable, independently verified evidence note."""
    checks = verify_item(item, category, line_map)
    source_line = item.get("source_line")
    evidence = item.get("evidence")

    text = f"  - Source line: {clean_text(source_line)}"
    text += f" | Verification: {checks['source_check']}"

    if isinstance(source_line, int) and source_line in line_map:
        original = redact_sensitive_text(line_map[source_line])
        text += f"\n    - Original evidence: `{original}`"
    elif isinstance(evidence, str) and evidence.strip():
        text += f"\n    - AI-provided evidence: `{redact_sensitive_text(evidence)}`"

    if category == "conflicts":
        related_line = item.get("related_source_line")
        text += f"\n  - Related source line: {clean_text(related_line)}"
        text += f" | Verification: {checks.get('related_source_check', 'NEEDS VERIFICATION')}"
        if isinstance(related_line, int) and related_line in line_map:
            related_original = redact_sensitive_text(line_map[related_line])
            text += f"\n    - Related evidence: `{related_original}`"

    return text


def format_item(item, category, line_map):
    """Format one extracted finding for the handover brief."""
    if not isinstance(item, dict):
        return f"- {clean_text(item)}"

    description = clean_text(item.get("item"), "Description not provided")
    lines = [f"- **{description}**"]

    if item.get("owner"):
        lines.append(f"  - Owner: {clean_text(item.get('owner'))}")

    if item.get("action_type"):
        lines.append(f"  - Action type: {clean_text(item.get('action_type'))}")

    if item.get("priority"):
        lines.append(f"  - Priority: {clean_text(item.get('priority'))}")

    if item.get("due_date"):
        lines.append(f"  - Due date: {clean_text(item.get('due_date'))}")

    if item.get("impact"):
        lines.append(f"  - Potential impact: {clean_text(item.get('impact'))}")

    if item.get("depends_on"):
        lines.append(f"  - Depends on: {clean_text(item.get('depends_on'))}")

    if item.get("confidence"):
        lines.append(f"  - AI confidence: {clean_text(item.get('confidence'))}")

    lines.append(format_evidence(item, line_map, category))
    return "\n".join(lines)


def render_section(report, category, title, line_map):
    """Render one report category into Markdown."""
    entries = safe_list(report.get(category))
    output = [f"## {title} ({len(entries)})"]

    if not entries:
        output.append("- No supported findings were extracted.")
    else:
        for item in entries:
            output.append(format_item(item, category, line_map))

    output.append("")
    return "\n".join(output)


# --------------------------------------------------
# 3. BUILD THE SMART HANDOVER BRIEF
# --------------------------------------------------

def build_brief(report, line_map):
    project_name = clean_text(report.get("project_name"), "Project name not identified")
    snapshot = report.get("project_snapshot")
    if not isinstance(snapshot, dict):
        snapshot = {}

    readiness = report.get("handover_readiness")
    if not isinstance(readiness, dict):
        readiness = {}

    evidence_total = 0
    evidence_matched = 0
    evidence_needs_review = 0

    for category in EVIDENCE_CATEGORIES:
        for item in safe_list(report.get(category)):
            evidence_total += 1
            checks = verify_item(item, category, line_map)
            if checks.get("source_check") == "MATCHED":
                evidence_matched += 1
            else:
                evidence_needs_review += 1
            if category == "conflicts" and checks.get("related_source_check") != "MATCHED":
                evidence_needs_review += 1

    lines = [
        f"# Incoming Member Handover Brief — {project_name}",
        "",
        "> **DRAFT — HUMAN REVIEW REQUIRED. Do not distribute until an authorised reviewer checks and approves it.**",
        "",
        "## 1. Project at a glance",
        f"- **Project:** {project_name}",
        f"- **Reported project status:** {clean_text(snapshot.get('status'), 'unknown')}",
        f"- **Handover readiness reported by AI:** {clean_text(readiness.get('status'), 'incomplete')}",
        f"- **Source file:** {SOURCE_FILE.name}",
        f"- **Evidence items checked:** {evidence_total}",
        f"- **Evidence matches:** {evidence_matched}",
        f"- **Evidence needing review:** {evidence_needs_review}",
        "",
        "## 2. Project summary",
        clean_text(snapshot.get("summary"), "The AI did not provide a project summary."),
        "",
    ]

    section_details = [
        ("completed", "Completed work"),
        ("pending", "Pending work"),
        ("decisions", "Recorded decisions"),
        ("blockers", "Current blockers"),
        ("risks", "Potential risks"),
        ("dependencies", "Dependencies"),
        ("next_actions", "Suggested or explicit next actions"),
        ("ownership_gaps", "Ownership gaps"),
        ("conflicts", "Conflicting information"),
    ]

    for category, title in section_details:
        lines.append(render_section(report, category, title, line_map))

    lines.extend(["## 3. Questions and missing information", ""])

    for field, heading in [
        ("needs_verification", "Needs verification"),
        ("missing_information", "Missing information"),
    ]:
        lines.append(f"### {heading}")
        entries = safe_list(report.get(field))
        if entries:
            for entry in entries:
                lines.append(f"- {clean_text(entry)}")
        else:
            lines.append("- None listed by the AI.")
        lines.append("")

    lines.extend([
        "## 4. Incoming member's first review steps",
        "1. Read the original meeting notes, not only this brief.",
        "2. Check every cited source line and confirm that the interpretation is accurate.",
        "3. Confirm task status, owners, deadlines, dependencies and blockers with the team.",
        "4. Resolve conflicts and items marked `NEEDS VERIFICATION`.",
        "5. Ask an authorised project lead to review the brief before it is shared.",
        "",
        "## 5. Human review status",
        "- **Status:** PENDING HUMAN REVIEW",
        "- **AI approval:** Not granted. This script cannot approve or share the handover.",
        "- **Review checklist:** See `handover_review_checklist.json`.",
        "",
        "---",
        "Generated locally by HandoverHub AI Day 7. This brief is a draft and may contain AI extraction errors.",
        "",
    ])

    return "\n".join(lines), evidence_total, evidence_matched, evidence_needs_review


# --------------------------------------------------
# 4. CREATE A HUMAN REVIEW CHECKLIST
# --------------------------------------------------

def build_review_checklist(project_name, evidence_total, evidence_matched, evidence_needs_review):
    return {
        "project_name": project_name,
        "review_status": "PENDING_HUMAN_REVIEW",
        "approved_for_sharing": False,
        "evidence_validation": {
            "total_items_checked": evidence_total,
            "matched_items": evidence_matched,
            "items_needing_review": evidence_needs_review,
        },
        "checklist": [
            {"task": "Read the original meeting notes", "checked": False},
            {"task": "Verify each source citation and its meaning", "checked": False},
            {"task": "Confirm completed and pending task status", "checked": False},
            {"task": "Confirm owners, priorities and deadlines", "checked": False},
            {"task": "Review blockers, risks and dependencies", "checked": False},
            {"task": "Resolve conflicts and missing information", "checked": False},
            {"task": "Check that no confidential information is included", "checked": False},
            {"task": "Obtain approval from an authorised project reviewer", "checked": False},
        ],
        "note": "This checklist is a draft. A human reviewer must complete it; the script does not approve or distribute the report.",
    }


# --------------------------------------------------
# 5. MAIN PROGRAM
# --------------------------------------------------

def main():
    print("========== HANDOVERHUB AI - DAY 7 ==========")
    print("Creating an incoming-member handover brief...\n")

    if not REPORT_FILE.exists():
        print("ERROR: handover_ai_report.json was not found.")
        print("First run day6.py successfully, then run day7.py.")
        return

    if not SOURCE_FILE.exists():
        print("ERROR: meeting_notes.txt was not found.")
        print("Keep it in the same folder as day7.py.")
        return

    try:
        report = read_json(REPORT_FILE)
        if not isinstance(report, dict):
            print("ERROR: The handover report must contain a JSON object.")
            return

        line_map = load_source_lines(SOURCE_FILE)
        if not line_map:
            print("ERROR: meeting_notes.txt is empty.")
            return

        brief, total, matched, needs_review = build_brief(report, line_map)

        project_name = clean_text(report.get("project_name"), "Project name not identified")
        checklist = build_review_checklist(
            project_name, total, matched, needs_review
        )

        BRIEF_FILE.write_text(brief, encoding="utf-8")
        REVIEW_FILE.write_text(
            json.dumps(checklist, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

        print("Evidence items checked:", total)
        print("Evidence matches:", matched)
        print("Items needing human review:", needs_review)
        print("\nSUCCESS! Files created:")
        print("1.", BRIEF_FILE.name)
        print("2.", REVIEW_FILE.name)
        print("\nReview status: PENDING HUMAN REVIEW")
        print("The script has NOT approved or shared the handover.")

    except json.JSONDecodeError as error:
        print("ERROR: handover_ai_report.json is not valid JSON.")
        print(error)
        print("Run day6.py again to generate a valid report.")

    except OSError as error:
        print("FILE ERROR:", error)

    except Exception as error:
        print("PROGRAM ERROR:", type(error).__name__, str(error))


if __name__ == "__main__":
    main()
