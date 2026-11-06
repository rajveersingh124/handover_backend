HANDOVERHUB AI - DAY 8 STREAMLIT DASHBOARD

1. Put app.py in the same folder as:
   - meeting_notes.txt
   - handover_ai_report.json
   - incoming_member_brief.md
   - handover_review_checklist.json

2. Open VS Code terminal in that folder.

3. Install the dashboard dependency:
   python -m pip install -r requirements.txt

4. Run the dashboard:
   python -m streamlit run app.py

5. Streamlit will show a local address and normally open the app in your browser.

To update dashboard data:
   a. Run: python day6.py
   b. Run: python day7.py
   c. Click "Refresh project files" in the dashboard.

IMPORTANT:
- app.py does not call APInex or any AI API.
- Keep .env private and do not upload it to a public repository.
- The dashboard does not approve or distribute a handover.
- Human review is required before sharing any handover report.
