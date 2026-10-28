"""Page 1: Saved Jobs - View and manage bookmarked opportunities."""

import os
import sys
from pathlib import Path
import urllib.parse

# Ensure application root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from config import APP_TITLE
from database import (
    init_db,
    get_applications,
    update_application_status,
    delete_application
)
from models import VALID_STATUSES, get_portal_info

init_db()

st.set_page_config(
    page_title=f"Saved Jobs - {APP_TITLE}",
    page_icon="⭐",
    layout="wide"
)

st.title("⭐ Saved Job Opportunities")
st.markdown("Manage your bookmarked opportunities, customize notes, and keep track of your career prospects.")

# Filters and search
f_col1, f_col2 = st.columns([1, 2])
with f_col1:
    selected_status = st.selectbox("Filter by Status", ["All Statuses"] + VALID_STATUSES)
with f_col2:
    search_query = st.text_input("Search Saved Jobs (by title, company, or notes)", placeholder="e.g. Data Engineer, Bengaluru")

# Fetch applications from SQLite
status_filter = None if selected_status == "All Statuses" else selected_status
apps = get_applications(status=status_filter)

# Filter by search query if provided
if search_query.strip():
    q = search_query.lower().strip()
    apps = [
        a for a in apps
        if q in a.title.lower() or q in a.company.lower() or q in a.location.lower() or q in a.notes.lower()
    ]

st.markdown(f"**Total Bookmarked Jobs: {len(apps)}**")
st.markdown("---")

if not apps:
    st.info(
        "💡 **No saved jobs found.** "
        "Head back to the **Dashboard** page, search for jobs using Playwright MCP, "
        "and click **'⭐ Save Job'** to bookmark them here!"
    )
else:
    for idx, app in enumerate(apps):
        with st.container():
            st.markdown("""
            <style>
                .app-card {
                    background: var(--secondary-background-color, #1a1f2c);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    padding: 18px;
                    margin-bottom: 14px;
                }
            </style>
            """, unsafe_allow_html=True)
            
            portal = get_portal_info(getattr(app, "url", ""), getattr(app, "notes", ""))
            with st.expander(f"📌 {app.title} — {app.company} [{app.status}]", expanded=True):
                # Small card mentioning which website the link was taken from
                st.markdown(f"""
                <div style="background-color: {portal['bg']}; border: 1.5px solid {portal['border']}; border-left: 5px solid {portal['color']}; border-radius: 8px; padding: 8px 14px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.2rem;">{portal['icon']}</span>
                        <div>
                            <span style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;">Job Source</span><br/>
                            <span style="font-size: 0.95rem; font-weight: 700; color: {portal['color']};">🌐 Link taken from <strong>{portal['full_name']}</strong></span>
                        </div>
                    </div>
                    <div>
                        <span style="background-color: rgba(255, 255, 255, 0.08); border: 1px solid {portal['border']}; color: {portal['color']}; font-size: 0.8rem; font-weight: 600; padding: 4px 10px; border-radius: 6px;">
                            🔗 {portal['domain']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**🏢 Company:** {app.company}")
                    st.markdown(f"**📍 Location:** {app.location} | **🎓 Experience:** {app.experience}")
                    if app.salary and app.salary != "Not Specified":
                        st.markdown(f"**💰 Salary:** {app.salary}")
                    st.markdown(f"**🕒 Saved on:** `{app.saved_at}` | **Last updated:** `{app.updated_at}`")
                    st.markdown(f"**📝 Description:**\n> {app.description}")
                
                with c2:
                    st.markdown("##### Update Status")
                    current_idx = VALID_STATUSES.index(app.status) if app.status in VALID_STATUSES else 0
                    new_status = st.selectbox(
                        "Application Status",
                        VALID_STATUSES,
                        index=current_idx,
                        key=f"status_select_{app.id}"
                    )
                    
                    if new_status != app.status:
                        if update_application_status(app.id, new_status):
                            st.success(f"Status updated to '{new_status}'!")
                            st.rerun()

                    safe_app_url = app.url if (app.url and app.url.startswith("http")) else f"https://www.google.com/search?q={urllib.parse.quote(f'{app.title} {app.company}')}"
                    st.link_button("🔗 Open Job Page", safe_app_url, use_container_width=True)

                # Notes section
                st.markdown("##### ✍️ Application Notes & Timeline")
                notes_key = f"notes_{app.id}"
                new_notes = st.text_area(
                    "Your personal notes (e.g. Applied via email, interview questions, follow-up dates)",
                    value=app.notes or "",
                    key=notes_key,
                    height=80
                )
                
                b1, b2, _ = st.columns([1, 1, 2])
                with b1:
                    if st.button("💾 Save Notes", key=f"save_notes_{app.id}"):
                        if update_application_status(app.id, app.status, notes=new_notes):
                            st.success("Notes saved!")
                            st.rerun()
                with b2:
                    if st.button("🗑️ Remove Job", key=f"del_{app.id}"):
                        if delete_application(app.id):
                            st.success("Job removed from saved list.")
                            st.rerun()
