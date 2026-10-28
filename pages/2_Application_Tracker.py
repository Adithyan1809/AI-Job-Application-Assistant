"""Page 2: Application Tracker - Track application statuses and pipeline metrics."""

import os
import sys
from pathlib import Path

# Ensure application root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from datetime import datetime

from config import APP_TITLE
from database import (
    init_db,
    get_applications,
    get_status_counts,
    update_application_status
)
from models import VALID_STATUSES, get_portal_info

init_db()

st.set_page_config(
    page_title=f"Application Tracker - {APP_TITLE}",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Job Application Tracker")
st.markdown("Monitor your career search funnel from initial bookmark to interviews and offers.")

# Get status counts
counts = get_status_counts()
total_apps = sum(counts.values())

# Metrics display
st.markdown("### 📈 Application Pipeline Overview")
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("📌 Interested", counts.get("Interested", 0))
with m2:
    st.metric("📤 Applied", counts.get("Applied", 0))
with m3:
    st.metric("🎙️ Interview", counts.get("Interview", 0))
with m4:
    st.metric("🎉 Offer", counts.get("Offer", 0))
with m5:
    st.metric("❌ Rejected", counts.get("Rejected", 0))

st.markdown("---")

# Pipeline progress
if total_apps > 0:
    active_in_pipeline = counts.get("Applied", 0) + counts.get("Interview", 0) + counts.get("Offer", 0)
    interview_rate = (counts.get("Interview", 0) + counts.get("Offer", 0)) / max(total_apps, 1) * 100
    offer_rate = counts.get("Offer", 0) / max(total_apps, 1) * 100
    
    st.markdown(f"**Pipeline Health:** `{total_apps}` Total Tracked | `{active_in_pipeline}` Active | **Interview Conversion Rate:** `{interview_rate:.1f}%`")
    st.progress(min(max(active_in_pipeline / total_apps, 0.0), 1.0))
else:
    st.info("No applications in tracker yet. Search jobs on the Dashboard and save them to begin tracking.")

# Application Table & Export
st.markdown("### 📑 All Tracked Applications")

apps = get_applications()

if apps:
    # Build dataframe for display
    data = []
    for a in apps:
        portal = get_portal_info(getattr(a, "url", ""), "")
        data.append({
            "ID": a.id,
            "Job Title": a.title,
            "Company": a.company,
            "Source Website": f"{portal['icon']} {portal['name']}",
            "Location": a.location,
            "Status": a.status,
            "Salary": a.salary,
            "Notes": a.notes,
            "Saved Date": a.saved_at,
            "Last Updated": a.updated_at,
            "Application URL": a.url
        })
    df = pd.DataFrame(data)

    # Interactive search & filter
    status_filter = st.multiselect("Filter Table by Status", VALID_STATUSES, default=VALID_STATUSES)
    filtered_df = df[df["Status"].isin(status_filter)]

    st.dataframe(
        filtered_df,
        column_config={
            "Application URL": st.column_config.LinkColumn("Application URL"),
            "Status": st.column_config.SelectboxColumn("Status", options=VALID_STATUSES, required=True),
        },
        use_container_width=True,
        hide_index=True
    )

    # Export to CSV
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Tracker to CSV",
        data=csv_bytes,
        file_name=f"job_applications_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    st.markdown("---")
    
    # Quick Status Update Form
    st.markdown("### ⚡ Quick Status Update")
    with st.form("quick_status_form"):
        col_sel, col_stat = st.columns(2)
        with col_sel:
            app_options = {f"{a.id}: {a.title} @ {a.company} ({a.status})": a.id for a in apps}
            selected_app_label = st.selectbox("Select Application", list(app_options.keys()))
            selected_app_id = app_options[selected_app_label]
        with col_stat:
            target_status = st.selectbox("New Status", VALID_STATUSES, index=1)

        quick_notes = st.text_input("Optional status update note (e.g. Sent follow-up email today)")
        submit_update = st.form_submit_button("Update Status")

        if submit_update:
            if update_application_status(selected_app_id, target_status, notes=quick_notes if quick_notes else None):
                st.success(f"Updated status of #{selected_app_id} to '{target_status}'!")
                st.rerun()

else:
    st.caption("Tracked applications will appear here in a structured, exportable table.")
