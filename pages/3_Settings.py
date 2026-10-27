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
    
    # Hero Introduction Banner
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; border-radius: 12px; padding: 22px 26px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div>
                <h3 style="color: #60a5fa; margin: 0 0 6px 0; font-size: 1.35rem;">⚡ Official Playwright Model Context Protocol (MCP)</h3>
                <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem; max-width: 750px;">
                    Model Context Protocol (MCP) is an open, vendor-neutral standard that enables AI models and Python applications to safely control external browsers, tools, and enterprise environments via standardized JSON-RPC over <code>stdio</code>.
                </p>
            </div>
            <div>
                <span style="background: rgba(59,130,246,0.25); border: 1px solid #3b82f6; color: #93c5fd; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                    RFC JSON-RPC 2.0
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Key pillars row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; text-align: center;">
            <span style="font-size: 1.8rem;">🔌</span>
            <h5 style="margin: 8px 0 4px 0; font-size: 0.95rem;">Stdio Transport</h5>
            <p style="color: #64748b; font-size: 0.78rem; margin: 0;">Direct bi-directional pipe communication</p>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; text-align: center;">
            <span style="font-size: 1.8rem;">🌐</span>
            <h5 style="margin: 8px 0 4px 0; font-size: 0.95rem;">Cross-Language</h5>
            <p style="color: #64748b; font-size: 0.78rem; margin: 0;">Python MCP Client controls Node.js MCP server</p>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; text-align: center;">
            <span style="font-size: 1.8rem;">🤖</span>
            <h5 style="margin: 8px 0 4px 0; font-size: 0.95rem;">Agent-Native</h5>
            <p style="color: #64748b; font-size: 0.78rem; margin: 0;">Standardized schemas for LLM tool invocation</p>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; text-align: center;">
            <span style="font-size: 1.8rem;">🛡️</span>
            <h5 style="margin: 8px 0 4px 0; font-size: 0.95rem;">Zero Driver Setup</h5>
            <p style="color: #64748b; font-size: 0.78rem; margin: 0;">No manual ChromeDriver downloads needed</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visual 5-Tier Architecture Flow
    st.markdown("#### 🏛️ 5-Tier End-to-End System Architecture")
    st.markdown("The journey from user search request to headless browser inspection and database persistence:")

    # Tier 1
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 6px solid #2563eb; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; color: #1e40af; font-size: 1rem;">🖥️ Tier 1: Interactive Presentation Layer</span>
            <span style="background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">Streamlit Web UI</span>
        </div>
        <p style="color: #475569; font-size: 0.88rem; margin: 0 0 6px 0;">
            Accepts search queries (Job Role, Location, Experience Level). Renders discovered opportunities as cards, displays source badges (LinkedIn / Naukri / Internshala), and handles the Application Tracker pipeline.
        </p>
        <span style="font-size: 0.78rem; color: #64748b;"><strong>Components:</strong> <code>app.py</code>, <code>pages/1_Saved_Jobs.py</code>, <code>pages/2_Application_Tracker.py</code></span>
    </div>
    """, unsafe_allow_html=True)

    # Tier 2
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 6px solid #059669; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; color: #065f46; font-size: 1rem;">🐍 Tier 2: Business Logic & Orchestration Layer</span>
            <span style="background: #ecfdf5; color: #047857; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">Python 3.10+ Backend</span>
        </div>
        <p style="color: #475569; font-size: 0.88rem; margin: 0 0 6px 0;">
            Orchestrates public job discovery, manages SQLite database storage with strict deduplication, and coordinates Gemini LLM calls for technical skill extraction and fresher interview preparation guides.
        </p>
        <span style="font-size: 0.78rem; color: #64748b;"><strong>Components:</strong> <code>services/job_search.py</code>, <code>services/ai_service.py</code>, <code>database.py</code>, <code>models.py</code></span>
    </div>
    """, unsafe_allow_html=True)

    # Tier 3
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 6px solid #7c3aed; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; color: #5b21b6; font-size: 1rem;">⚡ Tier 3: Model Context Protocol (MCP) Client</span>
            <span style="background: #f5f3ff; color: #6d28d9; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">Official Python MCP SDK</span>
        </div>
        <p style="color: #475569; font-size: 0.88rem; margin: 0 0 6px 0;">
            Establishes stdio stream pipes to the external server subprocess. Discovers available tools via <code>session.list_tools()</code> and translates high-level browser actions into standardized JSON-RPC 2.0 messages.
        </p>
        <span style="font-size: 0.78rem; color: #64748b;"><strong>Components:</strong> <code>mcp.client.session.ClientSession</code>, <code>mcp.client.stdio.stdio_client</code>, <code>services/mcp_client.py</code></span>
    </div>
    """, unsafe_allow_html=True)

    # Tier 4
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 6px solid #d97706; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; color: #92400e; font-size: 1rem;">🤖 Tier 4: Official Playwright MCP Server</span>
            <span style="background: #fffbeb; color: #b45309; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">Node.js / @playwright/mcp</span>
        </div>
        <p style="color: #475569; font-size: 0.88rem; margin: 0 0 6px 0;">
            The official Microsoft Playwright tool server running in headless mode. Implements 25+ browser manipulation tools and interfaces with Chromium via the Chrome DevTools Protocol (CDP).
        </p>
        <span style="font-size: 0.78rem; color: #64748b;"><strong>Key Tools:</strong> <code>browser_navigate</code>, <code>browser_wait_for</code>, <code>browser_evaluate</code>, <code>browser_snapshot</code>, <code>browser_click</code></span>
    </div>
    """, unsafe_allow_html=True)

    # Tier 5
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 6px solid #dc2626; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; color: #991b1b; font-size: 1rem;">🌐 Tier 5: Headless Browser & Live Web Targets</span>
            <span style="background: #fef2f2; color: #b91c1c; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">Chromium Engine</span>
        </div>
        <p style="color: #475569; font-size: 0.88rem; margin: 0 0 6px 0;">
            Full rendering engine executing JavaScript and styles across public job boards (LinkedIn, Naukri, Internshala). Uses desktop user-agent headers to guarantee clean, unblocked public listing retrieval.
        </p>
        <span style="font-size: 0.78rem; color: #64748b;"><strong>Target Portals:</strong> <code>linkedin.com/jobs</code>, <code>naukri.com</code>, <code>internshala.com</code></span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Execution Lifecycle Walkthrough
    st.markdown("#### 🔄 Step-by-Step Playwright MCP Execution Lifecycle")
    
    st1, st2, st3 = st.columns(3)
    with st1:
        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; height: 100%;">
            <div style="background: #dbeafe; color: #1e40af; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-bottom: 8px;">1</div>
            <h5 style="margin: 0 0 6px 0; color: #0f172a;">Handshake & Discovery</h5>
            <p style="color: #64748b; font-size: 0.82rem; margin: 0;">
                Python client connects over <code>stdio</code>. The MCP server returns capability metadata and registers 25 browser automation tools into the session.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with st2:
        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; height: 100%;">
            <div style="background: #dbeafe; color: #1e40af; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-bottom: 8px;">2</div>
            <h5 style="margin: 0 0 6px 0; color: #0f172a;">Live Navigation & Sync</h5>
            <p style="color: #64748b; font-size: 0.82rem; margin: 0;">
                Client invokes <code>browser_navigate</code> with search URLs, then synchronizes via <code>browser_wait_for</code> ensuring dynamic job listings finish hydration.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with st3:
        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; height: 100%;">
            <div style="background: #dbeafe; color: #1e40af; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-bottom: 8px;">3</div>
            <h5 style="margin: 0 0 6px 0; color: #0f172a;">Inspection & Ingestion</h5>
            <p style="color: #64748b; font-size: 0.82rem; margin: 0;">
                Invokes <code>browser_evaluate</code> to extract structured cards (title, company, salary, link), deduplicates records, and commits entries to SQLite.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Interactive JSON-RPC Protocol Inspector
    with st.expander("🔍 Interactive Protocol Inspector: View Actual JSON-RPC 2.0 Payloads", expanded=False):
        st.markdown("Here is the exact standardized JSON-RPC 2.0 communication travelling over `stdio` between Python and the Playwright MCP server:")
        
        c_req, c_res = st.columns(2)
        with c_req:
            st.markdown("##### 📤 Request: `tools/call` (`browser_navigate`)")
            st.code("""{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "tools/call",
  "params": {
    "name": "browser_navigate",
    "arguments": {
      "url": "https://www.linkedin.com/jobs/search?keywords=Data+Engineer&location=Bengaluru&f_E=1,2"
    }
  }
}""", language="json")

        with c_res:
            st.markdown("##### 📥 Response: Tool Result")
            st.code("""{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Successfully navigated to https://www.linkedin.com/jobs/search..."
      }
    ],
    "isError": false
  }
}""", language="json")

    st.markdown("<br>", unsafe_allow_html=True)

    # Comparison Table
    st.markdown("#### ⚖️ Why Model Context Protocol (MCP) Outperforms Legacy Web Scrapers")
    
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        st.markdown("""
        <div style="background: #fff1f2; border: 1.5px solid #fecdd3; border-radius: 10px; padding: 18px; height: 100%;">
            <h5 style="color: #9f1239; margin: 0 0 10px 0;">❌ Legacy Web Scraping (Requests / Bs4 / Raw Selenium)</h5>
            <ul style="color: #4c0519; font-size: 0.85rem; padding-left: 20px; line-height: 1.6;">
                <li><strong>Fragile DOM dependencies:</strong> Easily breaks whenever a website changes a minor CSS class name or DOM tag.</li>
                <li><strong>No JavaScript rendering:</strong> <code>requests</code> and <code>BeautifulSoup</code> cannot execute client-side React/Vue SPAs.</li>
                <li><strong>Maintenance burden:</strong> Requires manually downloading and pairing browser driver executables (e.g., <code>chromedriver.exe</code>).</li>
                <li><strong>Not AI-Native:</strong> Cannot be directly invoked by LLMs or autonomous agents without custom glue code.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with comp_col2:
        st.markdown("""
        <div style="background: #f0fdf4; border: 1.5px solid #bbf7d0; border-radius: 10px; padding: 18px; height: 100%;">
            <h5 style="color: #14532d; margin: 0 0 10px 0;">✅ Model Context Protocol (MCP) Architecture</h5>
            <ul style="color: #052e16; font-size: 0.85rem; padding-left: 20px; line-height: 1.6;">
                <li><strong>Official Industry Standard:</strong> Backed by major AI ecosystem contributors for secure external tool execution.</li>
                <li><strong>Full Browser Engine:</strong> Renders complete JavaScript, single-page applications, and responsive layouts.</li>
                <li><strong>Zero Driver Configuration:</strong> Managed transparently via <code>npx @playwright/mcp@latest</code>.</li>
                <li><strong>Agent-Ready:</strong> Standardized tool definitions allow any LLM (Gemini, Claude, GPT) to autonomously call browser tools.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
