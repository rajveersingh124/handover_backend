# HandoverHub AI - Day 8
# Local Streamlit dashboard for Day 6 and Day 7 outputs.
# This dashboard reads local files only; it does not call an AI API.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


# ------------------------------------------------------------
# 1. APP SETTINGS AND PROJECT FILES
# ------------------------------------------------------------

st.set_page_config(
    page_title="HandoverHub AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
REPORT_FILE = BASE_DIR / "handover_ai_report.json"
SOURCE_FILE = BASE_DIR / "meeting_notes.txt"
BRIEF_FILE = BASE_DIR / "incoming_member_brief.md"
REVIEW_FILE = BASE_DIR / "handover_review_checklist.json"

CATEGORIES = {
    "completed": "Completed work",
    "pending": "Pending work",
    "decisions": "Recorded decisions",
    "blockers": "Current blockers",
    "risks": "Potential risks",
    "dependencies": "Dependencies",
    "next_actions": "Next actions",
    "ownership_gaps": "Ownership gaps",
    "conflicts": "Conflicting information",
}


# ------------------------------------------------------------
# 2. HELPERS
# ------------------------------------------------------------

def read_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Read a JSON object safely. Return (data, error)."""
    if not path.exists():
        return None, f"{path.name} was not found."

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            return None, f"{path.name} must contain a JSON object."
        return data, None
    except json.JSONDecodeError as error:
        return None, f"{path.name} is not valid JSON: {error}"
    except OSError as error:
        return None, f"Could not read {path.name}: {error}"


def read_text_file(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, f"{path.name} was not found."
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except OSError as error:
        return None, f"Could not read {path.name}: {error}"


def read_source_lines(path: Path) -> dict[int, str]:
    if not path.exists():
        return {}
    try:
        raw_lines = path.read_text(encoding="utf-8-sig").splitlines()
        return {number: line for number, line in enumerate(raw_lines, start=1)}
    except OSError:
        return {}


def as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def display_text(value: Any, fallback: str = "Not provided") -> str:
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).strip()


def item_title(item: Any) -> str:
    if isinstance(item, dict):
        return display_text(item.get("item"), "Description not provided")
    return display_text(item)


def verify_source_line(source_line: Any, evidence: Any, source_lines: dict[int, str]) -> bool:
    """Verify that the supplied evidence exactly matches the cited original line."""
    if isinstance(source_line, bool) or not isinstance(evidence, str):
        return False
    try:
        number = int(source_line)
    except (TypeError, ValueError):
        return False
    if number not in source_lines:
        return False
    return evidence.strip() == source_lines[number].strip()


def evidence_status(item: Any, category: str, source_lines: dict[int, str]) -> tuple[str, str | None]:
    if not isinstance(item, dict):
        return "NEEDS VERIFICATION", None

    main_ok = verify_source_line(
        item.get("source_line"), item.get("evidence"), source_lines
    )

    if category == "conflicts":
        related_ok = verify_source_line(
            item.get("related_source_line"),
            item.get("related_evidence"),
            source_lines,
        )
        if not (main_ok and related_ok):
            return "NEEDS VERIFICATION", "Both sides of a conflict must match source notes."
        return "MATCHED", None

    if main_ok:
        return "MATCHED", None
    return "NEEDS VERIFICATION", "The citation is missing or does not exactly match the source line."


def count_evidence(report: dict[str, Any], source_lines: dict[int, str]) -> tuple[int, int, int]:
    total = matched = 0
    for category in CATEGORIES:
        for item in as_list(report.get(category)):
            total += 1
            status, _ = evidence_status(item, category, source_lines)
            if status == "MATCHED":
                matched += 1
    return total, matched, total - matched


def render_item(item: Any, category: str, source_lines: dict[int, str], index: int) -> None:
    """Render a finding with its source verification details."""
    title = item_title(item)
    if not isinstance(item, dict):
        st.write(f"- {title}")
        return

    status, reason = evidence_status(item, category, source_lines)
    source_number = item.get("source_line", "Not provided")

    with st.expander(f"{index}. {title}", expanded=False):
        meta_left, meta_right = st.columns(2)
        with meta_left:
            st.caption(f"Source line: {source_number}")
        with meta_right:
            if status == "MATCHED":
                st.success("Evidence matched")
            else:
                st.warning("Needs verification")

        detail_fields = [
            ("Owner", "owner"),
            ("Action type", "action_type"),
            ("Priority", "priority"),
            ("Due date", "due_date"),
            ("Impact", "impact"),
            ("Depends on", "depends_on"),
            ("Confidence", "confidence"),
        ]
        for label, key in detail_fields:
            value = item.get(key)
            if value not in (None, "", []):
                st.write(f"**{label}:** {value}")

        if status == "MATCHED":
            line_number = int(item["source_line"])
            st.code(f"L{line_number} | {source_lines[line_number]}", language="text")
        else:
            if item.get("evidence"):
                st.write("**AI-provided evidence:**")
                st.code(str(item.get("evidence")), language="text")
            if reason:
                st.caption(reason)

        if category == "conflicts":
            related_number = item.get("related_source_line")
            related_ok = verify_source_line(
                related_number, item.get("related_evidence"), source_lines
            )
            st.write(f"**Related source line:** {display_text(related_number)}")
            if related_ok:
                number = int(related_number)
                st.code(f"L{number} | {source_lines[number]}", language="text")
            elif item.get("related_evidence"):
                st.warning("Related evidence needs verification.")
                st.code(str(item.get("related_evidence")), language="text")


def render_category(report: dict[str, Any], category: str, source_lines: dict[int, str]) -> None:
    entries = as_list(report.get(category))
    st.subheader(f"{CATEGORIES.get(category, category.title())} ({len(entries)})")
    if not entries:
        st.info("No supported findings were included in this category.")
        return
    for index, item in enumerate(entries, start=1):
        render_item(item, category, source_lines, index)


def create_default_review() -> dict[str, Any]:
    default_tasks = [
        "Read the original meeting notes",
        "Verify each source citation and its meaning",
        "Confirm completed and pending task status",
        "Confirm owners, priorities and deadlines",
        "Review blockers, risks and dependencies",
        "Resolve conflicts and missing information",
        "Check that no confidential information is included",
        "Obtain approval from an authorised project reviewer",
    ]
    return {
        "project_name": "Project not identified",
        "review_status": "PENDING_HUMAN_REVIEW",
        "approved_for_sharing": False,
        "checklist": [{"task": task, "checked": False} for task in default_tasks],
        "note": "Completing this checklist does not itself approve or share the handover.",
    }


# ------------------------------------------------------------
# 3. LOAD THE CURRENT PROJECT FILES
# ------------------------------------------------------------

report, report_error = read_json_file(REPORT_FILE)
brief_text, brief_error = read_text_file(BRIEF_FILE)
review_data, review_error = read_json_file(REVIEW_FILE)
source_lines = read_source_lines(SOURCE_FILE)

if report is None:
    report = {}
if review_data is None:
    review_data = create_default_review()

project_name = display_text(report.get("project_name"), "HandoverHub AI")
snapshot = report.get("project_snapshot")
if not isinstance(snapshot, dict):
    snapshot = {}
readiness = report.get("handover_readiness")
if not isinstance(readiness, dict):
    readiness = {}

completed_count = len(as_list(report.get("completed")))
pending_count = len(as_list(report.get("pending")))
blocker_count = len(as_list(report.get("blockers")))
risk_count = len(as_list(report.get("risks")))
evidence_total, evidence_matched, evidence_review = count_evidence(report, source_lines)


# ------------------------------------------------------------
# 4. STYLE
# ------------------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem; padding-bottom: 3rem;}
    .hero {
        padding: 1.35rem 1.5rem;
        border-radius: 18px;
        background: linear-gradient(115deg, #12233f 0%, #1c4770 60%, #176b72 100%);
        color: white;
        margin-bottom: 1.1rem;
    }
    .hero h1 {color: white; margin: 0; font-size: 2rem;}
    .hero p {color: #d8e7f5; margin: .35rem 0 0 0;}
    .small-muted {color: #8090a4; font-size: .86rem;}
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128, 145, 165, .25);
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(128, 145, 165, .05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# 5. SIDEBAR NAVIGATION
# ------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🧠 HandoverHub AI")
    st.caption("Evidence-first project handover")
    page = st.radio(
        "Workspace",
        [
            "Overview",
            "Work tracker",
            "Risks & dependencies",
            "Evidence explorer",
            "Handover brief",
            "Human review",
        ],
    )
    st.divider()
    st.markdown("**Project files**")
    file_states = [
        ("meeting_notes.txt", SOURCE_FILE.exists()),
        ("handover_ai_report.json", REPORT_FILE.exists()),
        ("incoming_member_brief.md", BRIEF_FILE.exists()),
        ("handover_review_checklist.json", REVIEW_FILE.exists()),
    ]
    for filename, exists in file_states:
        st.write(("🟢 " if exists else "⚪ ") + filename)
    st.divider()
    st.caption("Local dashboard • No AI API request is made from this page")
    if st.button("Refresh project files", use_container_width=True):
        st.rerun()


# ------------------------------------------------------------
# 6. HEADER AND DATA WARNINGS
# ------------------------------------------------------------

st.markdown(
    f"""
    <div class="hero">
      <h1>HandoverHub AI</h1>
      <p>Turn scattered project knowledge into a clear, evidence-linked handover.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if report_error:
    st.warning(report_error)
    st.info("First run `day6.py` successfully to generate the AI report. Then run `day7.py` to create the handover brief.")

if SOURCE_FILE.exists() is False:
    st.warning("meeting_notes.txt is missing. Evidence verification cannot run until the source notes are in this folder.")

if report and report.get("human_review_required") is not True:
    st.warning("The report does not explicitly mark human review as required. Treat it as an unapproved draft.")


# ------------------------------------------------------------
# 7. PAGES
# ------------------------------------------------------------

if page == "Overview":
    st.title(project_name)
    st.caption("Project command centre")

    status = display_text(snapshot.get("status"), "unknown").replace("_", " ").title()
    readiness_status = display_text(readiness.get("status"), "incomplete").replace("_", " ").title()

    metric_cols = st.columns(4)
    metric_cols[0].metric("Completed", completed_count)
    metric_cols[1].metric("Pending", pending_count)
    metric_cols[2].metric("Blockers", blocker_count)
    metric_cols[3].metric("Risks", risk_count)

    st.divider()
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Project snapshot")
        st.write(display_text(snapshot.get("summary"), "No project summary is available yet."))
        st.write(f"**Project status:** {status}")
        st.write(f"**Handover readiness:** {readiness_status}")
        if snapshot.get("supporting_source_lines"):
            st.caption("Snapshot source lines: " + ", ".join(str(x) for x in snapshot["supporting_source_lines"]))
    with right:
        st.subheader("Evidence health")
        st.metric("Evidence matches", f"{evidence_matched} / {evidence_total}")
        if evidence_review:
            st.warning(f"{evidence_review} item(s) need source verification.")
        elif evidence_total:
            st.success("All checked evidence items match the source notes.")
        else:
            st.info("Evidence counts will appear after Day 6 generates a report and the source notes are available.")

    st.divider()
    st.subheader("What needs attention")
    attention_col1, attention_col2 = st.columns(2)
    with attention_col1:
        st.markdown("**Pending work**")
        for item in as_list(report.get("pending"))[:5]:
            st.write("• " + item_title(item))
        if not as_list(report.get("pending")):
            st.caption("No pending items listed.")
    with attention_col2:
        st.markdown("**Current blockers**")
        for item in as_list(report.get("blockers"))[:5]:
            st.write("• " + item_title(item))
        if not as_list(report.get("blockers")):
            st.caption("No blockers listed.")

    st.info("Draft only: AI findings must be checked by an authorised human reviewer before the handover is shared.")

elif page == "Work tracker":
    st.title("Work tracker")
    st.caption("See what is complete, what remains, and which decisions were recorded.")
    tab1, tab2, tab3 = st.tabs(["Tasks", "Decisions", "Blockers"])
    with tab1:
        render_category(report, "completed", source_lines)
        st.divider()
        render_category(report, "pending", source_lines)
    with tab2:
        render_category(report, "decisions", source_lines)
    with tab3:
        render_category(report, "blockers", source_lines)

elif page == "Risks & dependencies":
    st.title("Risks & dependencies")
    st.caption("Review future risks, linked work, suggested actions, and missing ownership.")
    tab1, tab2, tab3 = st.tabs(["Risks", "Dependencies & actions", "Gaps & conflicts"])
    with tab1:
        render_category(report, "risks", source_lines)
    with tab2:
        render_category(report, "dependencies", source_lines)
        st.divider()
        render_category(report, "next_actions", source_lines)
    with tab3:
        render_category(report, "ownership_gaps", source_lines)
        st.divider()
        render_category(report, "conflicts", source_lines)
        st.divider()
        st.subheader("Missing information")
        missing = as_list(report.get("missing_information"))
        if missing:
            for entry in missing:
                st.write("• " + display_text(entry))
        else:
            st.info("No missing-information items were listed.")
        st.subheader("Needs verification")
        questions = as_list(report.get("needs_verification"))
        if questions:
            for entry in questions:
                st.write("• " + display_text(entry))
        else:
            st.info("No additional verification questions were listed.")

elif page == "Evidence explorer":
    st.title("Evidence explorer")
    st.caption("Check an AI finding against the exact original line in meeting_notes.txt.")
    available_categories = [key for key in CATEGORIES if as_list(report.get(key))]
    if not source_lines:
        st.warning("Original meeting notes are not available. Evidence cannot be independently checked.")
    if not available_categories:
        st.info("No findings are available yet. Run day6.py first.")
    else:
        selected = st.selectbox(
            "Choose a category",
            available_categories,
            format_func=lambda key: CATEGORIES[key],
        )
        entries = as_list(report.get(selected))
        matched_count = sum(
            1 for entry in entries
            if evidence_status(entry, selected, source_lines)[0] == "MATCHED"
        )
        st.metric("Matched evidence in this category", f"{matched_count} / {len(entries)}")
        for index, item in enumerate(entries, start=1):
            render_item(item, selected, source_lines, index)

elif page == "Handover brief":
    st.title("Incoming member handover brief")
    st.caption("The Day 7 report is a draft for review, not an approval or permission to share.")
    if brief_text:
        st.markdown(brief_text)
        st.download_button(
            "Download handover brief",
            data=brief_text,
            file_name="incoming_member_brief.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.warning(brief_error or "The handover brief is not available yet.")
        st.info("Run day7.py after day6.py to generate incoming_member_brief.md.")

    if report:
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        st.download_button(
            "Download AI report (JSON)",
            data=report_json,
            file_name="handover_ai_report.json",
            mime="application/json",
        )

elif page == "Human review":
    st.title("Human review")
    st.caption("Record review progress. This dashboard never approves or distributes the handover.")

    if review_error and REVIEW_FILE.exists():
        st.warning(review_error)

    checklist = as_list(review_data.get("checklist"))
    if not checklist:
        review_data = create_default_review()
        checklist = as_list(review_data.get("checklist"))

    st.warning("Checking every item below does not automatically authorise sharing. Approval must come from the authorised project reviewer through your team's process.")

    checked_values = []
    for index, entry in enumerate(checklist):
        if isinstance(entry, dict):
            task = display_text(entry.get("task"), f"Review item {index + 1}")
            default_checked = bool(entry.get("checked", False))
        else:
            task = display_text(entry, f"Review item {index + 1}")
            default_checked = False

        value = st.checkbox(task, value=default_checked, key=f"day8_review_{index}")
        checked_values.append({"task": task, "checked": value})

    done_count = sum(1 for entry in checked_values if entry["checked"])
    st.progress(done_count / max(len(checked_values), 1))
    st.caption(f"Review checklist progress: {done_count} of {len(checked_values)}")

    if st.button("Save review progress", type="primary", use_container_width=True):
        all_checked = bool(checked_values) and all(entry["checked"] for entry in checked_values)
        any_checked = any(entry["checked"] for entry in checked_values)
        if all_checked:
            saved_status = "REVIEW_CHECKLIST_COMPLETED_PENDING_SEPARATE_APPROVAL"
        elif any_checked:
            saved_status = "IN_PROGRESS"
        else:
            saved_status = "PENDING_HUMAN_REVIEW"

        updated_review = {
            "project_name": project_name,
            "review_status": saved_status,
            "approved_for_sharing": False,
            "checklist": checked_values,
            "note": "Saved locally by the dashboard. Completing the checklist does not approve or distribute the handover.",
        }

        try:
            REVIEW_FILE.write_text(
                json.dumps(updated_review, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
            st.success("Review progress saved locally. Sharing approval remains false.")
        except OSError as error:
            st.error(f"Could not save review progress: {error}")

    st.divider()
    st.write("**Current review status:** " + display_text(review_data.get("review_status"), "PENDING_HUMAN_REVIEW"))
    st.write("**Approved for sharing:** No")


# ------------------------------------------------------------
# 8. FOOTER
# ------------------------------------------------------------

st.divider()
st.caption(
    "HandoverHub AI • Day 8 dashboard. AI-generated findings may be incomplete or incorrect. "
    "Always verify source evidence and obtain authorised human review before sharing."
)
