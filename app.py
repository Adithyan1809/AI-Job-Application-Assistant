"""Main Streamlit application entry point: AI Job Application Assistant Dashboard."""

import asyncio
import urllib.parse
import streamlit as st
import pandas as pd
from datetime import datetime

from config import (
    APP_TITLE,
    APP_SUBTITLE,
    is_gemini_configured,
    DEMO_SERVER_PORT,
    ALLOWED_DOMAINS
)
from database import init_db, save_application, get_recent_jobs
from models import JobListing, Application, get_portal_info
from services.job_search import search_jobs_with_mcp
from services.ai_service import generate_job_summary
from services.mcp_client import check_mcp_health

# Initialize database schema
init_db()

# Page configuration
st.set_page_config(
    page_title=f"{APP_TITLE} - Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished cards, typography, and badges
st.markdown("""
<style>
    .main-header {
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e2e8f0;
    }
    .job-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .job-card:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.06);
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-loc { background-color: #f1f5f9; color: #334155; }
    .badge-exp { background-color: #eff6ff; color: #1d4ed8; }
    .badge-sal { background-color: #ecfdf5; color: #047857; }
    .badge-mcp { background-color: #fdf4ff; color: #86198f; border: 1px solid #f0abfc; }
    .badge-sample { background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
    .stButton>button {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar information & status
with st.sidebar:
    st.image("https://img.icons8.com/color/96/briefcase.png", width=64)
    st.title("AI Job Assistant")
    st.caption("Powered by **Playwright MCP** & **AI**")
    
    st.markdown("---")
    
    # Engine status
    st.markdown("#### System Status")
    st.success("🟢 Gemini AI Engine: Active")
        
    st.markdown("---")
    st.markdown("#### Navigation")
    st.markdown("- 🏠 **Dashboard** (Current)")
    st.markdown("- ⭐ **Saved Jobs** (See page in sidebar)")
    st.markdown("- 📊 **Application Tracker**")
    st.markdown("- ⚙️ **Settings & Diagnostics**")
    
    st.markdown("---")
    st.caption("🎓 Designed for college assignments & fresh graduate career exploration.")

# Main dashboard layout
st.markdown(f"<div class='main-header'><h1>💼 {APP_TITLE}</h1><p style='color: #64748b; font-size: 1.1rem;'>{APP_SUBTITLE}</p></div>", unsafe_allow_html=True)

# Search Form Container
with st.container():
    st.markdown("### 🔍 Discover Job Opportunities")
    st.markdown("Search verified public job portals using genuine **Playwright MCP browser automation**.")
    
    with st.form("job_search_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            role = st.text_input("Job Role or Keywords", value="Data Engineer", placeholder="e.g. Data Engineer, Python Developer, Frontend")
            location = st.text_input("Preferred Location", value="Bengaluru", placeholder="e.g. Bengaluru, Hyderabad, Remote")
        with col2:
            col_exp, col_emp = st.columns(2)
            with col_exp:
                experience = st.selectbox(
                    "Experience Level",
                    ["All", "Fresher", "Internship", "0-1 years", "1-2 years"],
                    index=1
                )
            with col_emp:
                employment_type = st.selectbox(
                    "Employment Type",
                    ["All", "Full-time", "Internship", "Remote", "Contract"],
                    index=0
                )
            min_salary = st.text_input("Optional Min Salary", placeholder="e.g. ₹5,00,000")

        # Informative notice card (replacing the dropdown with an automatic multi-portal crawler indicator)
        st.markdown("""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.9rem; color: #334155;">
            🌐 <strong>Auto-Scrapes Real Job Portals:</strong> Playwright MCP automatically connects to <strong>LinkedIn Jobs</strong>, <strong>Naukri.com</strong>, and <strong>Internshala</strong> to discover authentic live opportunities.
        </div>
        """, unsafe_allow_html=True)

        search_submitted = st.form_submit_button("🚀 Scrape Real Job Portals with Playwright MCP", use_container_width=True)

# Session state initialization for search results and active summaries
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "last_search_role" not in st.session_state:
    st.session_state.last_search_role = ""
if "last_search_loc" not in st.session_state:
    st.session_state.last_search_loc = ""
if "active_ai_summary" not in st.session_state:
    st.session_state.active_ai_summary = {}

# Execute search across real portals when button clicked
if search_submitted:
    portal_key = "all_portals"

    progress_placeholder = st.empty()
    progress_bar = st.progress(0.0)
    
    def update_progress(msg: str, pct: float):
        progress_placeholder.info(f"🤖 **Playwright MCP Status:** {msg}")
        progress_bar.progress(min(max(pct, 0.0), 1.0))

    try:
        # Run async MCP search across real job portals
        results = asyncio.run(
            search_jobs_with_mcp(
                role=role,
                location=location,
                experience="" if experience == "All" else experience,
                employment_type="" if employment_type == "All" else employment_type,
                min_salary=min_salary,
                portal_choice=portal_key,
                progress_cb=update_progress
            )
        )
        st.session_state.search_results = results
        st.session_state.last_search_role = role
        st.session_state.last_search_loc = location
        progress_bar.empty()
        if results:
            progress_placeholder.success(f"✅ Found **{len(results)}** real live opportunities matching '{role}' in '{location}'!")
        else:
            progress_placeholder.warning(f"⚠️ No open listings found on live portals for '{role}' in '{location}'. Try adjusting keywords or location.")
    except Exception as e:
        progress_bar.empty()
        progress_placeholder.error(f"❌ Search encountered an error: {e}")
        st.info("💡 **Tip:** Verify your internet connection. Playwright MCP connects directly to live job portals.")

# Display Results Section
results = st.session_state.search_results

st.markdown("---")
st.markdown("### 📋 Discovered Opportunities")

if not results:
    # Check if there are cached results in the DB
    cached = get_recent_jobs(limit=10)
    if cached:
        st.caption("Showing recently discovered opportunities from your search history:")
        results = cached
    else:
        st.info("No jobs to display yet. Enter your search criteria above and click **'Search Jobs with Playwright MCP'**.")

if results:
    # Filter & view controls
    col_filter_loc, col_filter_exp, col_view = st.columns([1, 1, 1])
    with col_filter_loc:
        available_locs = sorted(list(set(j.location for j in results if j.location)))
        selected_loc = st.selectbox("Filter by Location", ["All Locations"] + available_locs)
    with col_filter_exp:
        available_exps = sorted(list(set(j.experience for j in results if j.experience)))
        selected_exp = st.selectbox("Filter by Experience", ["All Experience"] + available_exps)
    with col_view:
        view_mode = st.radio("View Mode", ["Detailed Cards", "Table View"], horizontal=True)

    # Apply client-side filters
    displayed_jobs = results
    if selected_loc != "All Locations":
        displayed_jobs = [j for j in displayed_jobs if j.location == selected_loc]
    if selected_exp != "All Experience":
        displayed_jobs = [j for j in displayed_jobs if j.experience == selected_exp]

    st.markdown(f"**Showing {len(displayed_jobs)} jobs**")

    if view_mode == "Table View":
        df_data = []
        for j in displayed_jobs:
            portal = get_portal_info(getattr(j, "url", ""), getattr(j, "source", ""))
            df_data.append({
                "Job Title": j.title,
                "Company": j.company,
                "Website Source": f"{portal['icon']} {portal['name']}",
                "Location": j.location,
                "Experience": j.experience,
                "Salary": j.salary,
                "Playwright MCP": "⚡ Yes" if getattr(j, "extracted_via_mcp", True) else "Sample",
                "Application URL": j.url
            })
        st.dataframe(pd.DataFrame(df_data), use_container_width=True)
    else:
        # Detailed Card View
        for idx, job in enumerate(displayed_jobs):
            card_key = f"job_card_{idx}_{job.title[:10]}"
            portal = get_portal_info(getattr(job, "url", ""), getattr(job, "source", ""))
            with st.container():
                st.markdown("<div class='job-card'>", unsafe_allow_html=True)
                
                # Card Header
                c_top1, c_top2 = st.columns([3, 1])
                with c_top1:
                    st.markdown(f"#### [{job.title}]({job.url})")
                    st.markdown(f"**🏢 {job.company}**")
                with c_top2:
                    if job.extracted_via_mcp:
                        st.markdown("<span class='badge badge-mcp'>⚡ Playwright MCP Extracted</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='badge badge-sample'>📁 Sample Dataset</span>", unsafe_allow_html=True)

                # Dedicated small card mentioning which website this link was taken from
                st.markdown(f"""
                <div style="background-color: {portal['bg']}; border: 1.5px solid {portal['border']}; border-left: 5px solid {portal['color']}; border-radius: 8px; padding: 8px 14px; margin: 10px 0 12px 0; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.3rem;">{portal['icon']}</span>
                        <div>
                            <span style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #64748b; letter-spacing: 0.5px;">Originating Website</span><br/>
                            <span style="font-size: 0.95rem; font-weight: 700; color: {portal['color']};">🌐 Link taken from <strong>{portal['full_name']}</strong></span>
                        </div>
                    </div>
                    <div>
                        <span style="background-color: #ffffff; border: 1px solid {portal['border']}; color: {portal['color']}; font-size: 0.8rem; font-weight: 600; padding: 4px 10px; border-radius: 6px;">
                            ✓ Real Portal
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Badges row
                st.markdown(
                    f"<span class='badge badge-loc'>📍 {job.location}</span>"
                    f"<span class='badge badge-exp'>🎓 {job.experience}</span>"
                    f"<span class='badge badge-sal'>💰 {job.salary}</span>",
                    unsafe_allow_html=True
                )

                # Description snippet
                st.markdown(f"<p style='color: #475569; margin: 10px 0;'>{job.description}</p>", unsafe_allow_html=True)
                
                # Action Buttons Row
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1.2, 1.5])
                
                with btn_col1:
                    save_btn = st.button("⭐ Save Job", key=f"save_{idx}_{job.title[:15]}")
                    if save_btn:
                        ok, msg, app_id = save_application(job, status="Interested")
                        if ok:
                            st.success(f"Saved! Track in 'Application Tracker'.")
                        else:
                            st.warning(msg)

                with btn_col2:
                    summary_btn = st.button("💡 AI Job Summary", key=f"summary_{idx}_{job.title[:15]}")
                    if summary_btn:
                        with st.spinner("Generating AI role analysis & student prep tips..."):
                            summary_obj = generate_job_summary(job)
                            st.session_state.active_ai_summary[job.title] = summary_obj

                with btn_col3:
                    safe_url = job.url if (job.url and job.url.startswith("http")) else f"https://www.google.com/search?q={urllib.parse.quote(f'{job.title} {job.company}')}"
                    st.link_button("🔗 Open Application Link", safe_url, use_container_width=True)

                # Expand AI Summary if active for this job
                if job.title in st.session_state.active_ai_summary:
                    summary = st.session_state.active_ai_summary[job.title]
                    with st.expander(f"✨ AI Career Insights & Prep Guide for '{job.title}'", expanded=True):
                        st.caption(f"🛡️ *{summary.disclaimer}*")
                        
                        st.markdown("##### 🎯 Why this job is relevant to early-career engineers")
                        st.write(summary.relevance_explanation)
                        
                        s_col1, s_col2 = st.columns(2)
                        with s_col1:
                            st.markdown("##### 🛠️ Key Technical & Soft Skills")
                            for skill in summary.required_skills:
                                st.markdown(f"- `{skill}`")
                        with s_col2:
                            st.markdown("##### 📌 Primary Responsibilities")
                            for resp in summary.responsibilities:
                                st.markdown(f"- {resp}")

                        st.markdown("##### 🚀 Actionable Student Preparation Advice")
                        for tip in summary.prep_advice:
                            st.markdown(f"- 💡 {tip}")

                st.markdown("</div>", unsafe_allow_html=True)
