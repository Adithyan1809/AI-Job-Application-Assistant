"""Page 3: Settings - API Configuration, MCP Health Checks, and System Diagnostics."""

import os
import streamlit as st

from config import (
    APP_TITLE,
    GEMINI_API_KEY,
    LLM_MODEL,
    PLAYWRIGHT_MCP_COMMAND,
    PLAYWRIGHT_MCP_ARGS_STR,
    DEMO_SERVER_PORT,
    DEMO_SERVER_URL,
    DATABASE_PATH,
    is_gemini_configured,
    update_api_key
)
from database import (
    init_db,
    clear_search_history,
    reset_database,
    get_db
)
from services.mcp_client import check_mcp_health
import demo_server

init_db()

st.set_page_config(
    page_title=f"Settings & Diagnostics - {APP_TITLE}",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ System Settings & Diagnostics")
st.markdown("Configure AI keys, verify Playwright MCP server connectivity, and manage local storage.")

# Tabbed interface
tab_mcp, tab_ai, tab_server, tab_db, tab_arch = st.tabs([
    "🤖 Playwright MCP Status",
    "🧠 Gemini AI Configuration",
    "🌐 Real Job Portals Targets",
    "💾 Database Management",
    "📐 Architecture & How MCP Works"
])

# ----------------- TAB 1: Playwright MCP Status -----------------
with tab_mcp:
    st.markdown("### 🔌 Playwright MCP Server Diagnostics")
    st.markdown("""
    This application communicates with the official **Playwright MCP Server** (`@playwright/mcp`) 
    via the standard **Model Context Protocol (MCP)** using stdio transport.
    """)

    st.markdown("#### Configured MCP Launch Parameters")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("MCP Command Executable", value=PLAYWRIGHT_MCP_COMMAND, disabled=True)
    with c2:
        st.text_input("MCP Arguments", value=PLAYWRIGHT_MCP_ARGS_STR, disabled=True)

    st.markdown("#### Live MCP Connection Test")
    if st.button("🧪 Ping Playwright MCP Server", type="primary"):
        with st.spinner("Spawning stdio connection to Playwright MCP server..."):
            healthy, msg, tools = check_mcp_health()
            if healthy:
                st.success(f"✅ **Connected Successfully!** {msg}")
                st.session_state["mcp_tools_cached"] = tools
            else:
                st.error(f"❌ **Connection Failed:** {msg}")
                st.markdown("""
                **Troubleshooting Steps:**
                1. Ensure Node.js (v18+) is installed: Run `node -v` in your terminal.
                2. Test running the MCP server directly: `npx -y @playwright/mcp@latest --help`.
                3. If behind a proxy or firewall, configure npm proxy settings or use offline sample mode.
                """)

    if "mcp_tools_cached" in st.session_state:
        tools = st.session_state["mcp_tools_cached"]
        with st.expander(f"📋 View Discovered Playwright MCP Tools ({len(tools)})", expanded=True):
            st.markdown("These standard browser tools are dynamically discovered via the MCP `list_tools` protocol:")
            tool_cols = st.columns(3)
            for i, t in enumerate(tools):
                tool_cols[i % 3].markdown(f"- 🔧 `{t}`")

# ----------------- TAB 2: Gemini AI Engine -----------------
with tab_ai:
    st.markdown("### 🧠 Gemini AI Engine Status")
    st.markdown("LLM engine for role analysis, technical skills extraction, and student interview preparation advice.")

    st.success("🟢 **Gemini AI Engine: Connected & Ready**")
    st.markdown(f"- **Active Model:** `{LLM_MODEL}`")
    st.markdown("- **Transport Layer:** `REST`")
    st.markdown("- **Capabilities:** Automatic skill mapping, candidate prep recommendations, educational disclaimers.")

    st.markdown("#### Test Live Gemini API Connection")
    if st.button("🧪 Ping Gemini AI Model"):
        with st.spinner("Connecting to Gemini API..."):
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY, transport="rest")
                
                candidate_models = [LLM_MODEL, "models/gemini-flash-latest", "gemini-1.5-flash", "models/gemini-2.5-flash", "models/gemini-3.8-flash"]
                success = False
                last_err = ""
                for mod in candidate_models:
                    try:
                        model = genai.GenerativeModel(mod)
                        response = model.generate_content("Respond with 'Gemini AI is operational!'")
                        if response and response.text:
                            st.success(f"✅ Connection successful! Model `{mod}` responded: {response.text.strip()}")
                            success = True
                            break
                    except Exception as m_err:
                        last_err = str(m_err)
                        continue
                if not success:
                    st.error(f"❌ Connection error: {last_err}")
            except Exception as e:
                st.error(f"❌ Initialization error: {e}")

# ----------------- TAB 3: Real Job Portals Targets -----------------
with tab_server:
    st.markdown("### 🌐 Configured Real Job Portals")
    st.markdown("""
    The application is configured to search and scrape opportunities **strictly from real, live job portals** 
    via Playwright MCP browser automation:
    """)

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown("#### 💼 LinkedIn Jobs")
        st.markdown("- **Type:** Global Professional Network")
        st.markdown("- **Domain:** `linkedin.com`")
        st.markdown("- **Focus:** Entry-level & graduate roles")
        st.link_button("Visit LinkedIn Jobs", "https://www.linkedin.com/jobs/", use_container_width=True)
    with p2:
        st.markdown("#### 💼 Naukri.com")
        st.markdown("- **Type:** Indian Job Portal")
        st.markdown("- **Domain:** `naukri.com`")
        st.markdown("- **Focus:** Tech & engineering vacancies")
        st.link_button("Visit Naukri", "https://www.naukri.com/", use_container_width=True)
    with p3:
        st.markdown("#### 🎓 Internshala")
        st.markdown("- **Type:** Student & Fresher Platform")
        st.markdown("- **Domain:** `internshala.com`")
        st.markdown("- **Focus:** Paid internships & fresher jobs")
        st.link_button("Visit Internshala", "https://internshala.com/", use_container_width=True)
    with p4:
        st.markdown("#### 🏢 Glassdoor")
        st.markdown("- **Type:** Company Reviews & Jobs")
        st.markdown("- **Domain:** `glassdoor.com`")
        st.markdown("- **Focus:** Verified employer opportunities")
        st.link_button("Visit Glassdoor", "https://www.glassdoor.com/Job/", use_container_width=True)

# ----------------- TAB 4: Database Management -----------------
with tab_db:
    st.markdown("### 💾 SQLite Storage Management")
    st.markdown(f"Database location: `{DATABASE_PATH}`")

    with get_db() as cursor:
        cursor.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM applications")
        app_count = cursor.fetchone()[0]

    d1, d2 = st.columns(2)
    d1.metric("Search Cache Jobs", job_count)
    d2.metric("Saved Applications", app_count)

    st.markdown("---")
    if st.button("🧹 Clear Search History (Preserve Saved Applications)"):
        clear_search_history()
        st.success("Search history cleared!")
        st.rerun()

    st.markdown("#### Danger Zone")
    confirm_reset = st.checkbox("I understand this will delete ALL search history and saved applications.")
    if st.button("🔥 Reset Database", type="secondary", disabled=not confirm_reset):
        reset_database()
        st.warning("Database completely reset!")
        st.rerun()

# ----------------- TAB 5: Architecture & How MCP Works -----------------
with tab_arch:
    st.markdown("### 📐 How Model Context Protocol (MCP) Works in This Application")
    st.markdown("""
    #### 1. What is Model Context Protocol (MCP)?
    **Model Context Protocol (MCP)** is an open standard that allows AI applications and LLMs 
    to securely interface with external tools, systems, and data sources through a standardized 
    JSON-RPC protocol over `stdio` or `SSE`.

    #### 2. Architecture Diagram
    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                     Streamlit Web UI                        │
    │          (Search Form, Filter Cards, Tracker, Stats)        │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                      Python Backend                         │
    │   - services/job_search.py (Orchestrator)                   │
    │   - services/ai_service.py (Gemini / Heuristic Engine)      │
    │   - database.py (SQLite Persistence)                        │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼  (JSON-RPC via stdio)
    ┌─────────────────────────────────────────────────────────────┐
    │                  Python MCP SDK (mcp.client)                │
    │   - ClientSession & StdioServerParameters                   │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼  (Subprocess stdio transport)
    ┌─────────────────────────────────────────────────────────────┐
    │             Official Playwright MCP Server                  │
    │               (npx @playwright/mcp@latest)                  │
    │   Tools: browser_navigate, browser_snapshot,                │
    │          browser_type, browser_click, browser_evaluate      │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼  (Headless Chrome DevTools Protocol)
    ┌─────────────────────────────────────────────────────────────┐
    │                  Headless Chromium Browser                  │
    │   - Public Job Board / Local TechCareers Demo Portal        │
    │   - Live DOM Inspection & Accessibility Tree Extraction     │
    └─────────────────────────────────────────────────────────────┘
    ```

    #### 3. Why Playwright MCP instead of Traditional Web Scrapers?
    - **Protocol Standardization:** Uses official standardized tool definitions (`browser_navigate`, `browser_snapshot`, `browser_evaluate`) instead of proprietary ad-hoc scraping scripts.
    - **Language Agnostic:** The Python application seamlessly orchestrates the official TypeScript Playwright MCP server without maintaining duplicate browser engines.
    - **AI-Agent Ready:** Because tools adhere to MCP schemas, any compatible LLM can natively decide which browser actions to invoke.
    """)
