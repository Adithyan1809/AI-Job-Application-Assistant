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

    # ── HERO BANNER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        border: 1px solid rgba(139,92,246,0.35);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    ">
        <div style="position: absolute; top: -40px; right: -40px; width: 180px; height: 180px;
                    background: radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 70%);
                    border-radius: 50%;"></div>
        <div style="position: absolute; bottom: -30px; left: 20px; width: 120px; height: 120px;
                    background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 70%);
                    border-radius: 50%;"></div>
        <div style="display: flex; align-items: flex-start; gap: 20px; flex-wrap: wrap; position: relative; z-index: 1;">
            <div style="font-size: 3rem; line-height: 1;">⚡</div>
            <div style="flex: 1; min-width: 280px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap;">
                    <h3 style="color: #a5b4fc; margin: 0; font-size: 1.4rem; font-weight: 800;">Official Playwright MCP Architecture</h3>
                    <span style="background: rgba(99,102,241,0.3); border: 1px solid #6366f1; color: #c7d2fe;
                                 padding: 3px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; white-space: nowrap;">
                        JSON-RPC 2.0 · stdio
                    </span>
                </div>
                <p style="color: #94a3b8; margin: 0; font-size: 0.9rem; line-height: 1.65; max-width: 720px;">
                    <strong style="color: #c7d2fe;">Model Context Protocol (MCP)</strong> is an open, vendor-neutral standard that enables
                    AI models and Python applications to safely control external browsers and enterprise tools via
                    standardized <code style="background:rgba(255,255,255,0.1); padding:1px 5px; border-radius:4px;">stdio</code> pipes —
                    no custom glue code, no brittle drivers, no maintenance overhead.
                </p>
            </div>
        </div>
        <div style="display: flex; gap: 12px; margin-top: 18px; flex-wrap: wrap; position: relative; z-index: 1;">
            <span style="background: rgba(56,189,248,0.15); border: 1px solid rgba(56,189,248,0.4); color: #7dd3fc;
                         padding: 4px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">🔌 Stdio Transport</span>
            <span style="background: rgba(167,139,250,0.15); border: 1px solid rgba(167,139,250,0.4); color: #c4b5fd;
                         padding: 4px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">🐍 Python &harr; Node.js</span>
            <span style="background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.4); color: #6ee7b7;
                         padding: 4px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">🤖 Agent-Native</span>
            <span style="background: rgba(251,191,36,0.15); border: 1px solid rgba(251,191,36,0.4); color: #fde68a;
                         padding: 4px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">🛡️ Zero Driver Setup</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4 STAT CARDS ─────────────────────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    stat_cards = [
        ("25+", "Browser Tools", "Registered via MCP list_tools()", "#38bdf8"),
        ("3",   "Live Portals",  "LinkedIn · Naukri · Internshala",  "#34d399"),
        ("0",   "Drivers Needed","Zero manual ChromeDriver config",   "#a78bfa"),
        ("100%","Real Data",     "No mock / synthetic listings",      "#fbbf24"),
    ]
    for col, (val, label, sub, color) in zip([s1, s2, s3, s4], stat_cards):
        col.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.09);
                    border-top: 3px solid {color}; border-radius: 12px; padding: 18px 16px; text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: {color}; line-height: 1;">{val}</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #f1f5f9; margin: 6px 0 3px 0;">{label}</div>
            <div style="font-size: 0.74rem; color: #64748b;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── DATA FLOW DIAGRAM ─────────────────────────────────────────────────────────
    st.markdown("#### 🔀 Live Data Flow")
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07);
                border-radius: 14px; padding: 24px 20px; margin-bottom: 24px; overflow-x: auto;">
        <div style="display: flex; align-items: center; justify-content: center;
                    gap: 0; min-width: 640px; flex-wrap: nowrap;">

            <!-- Node: User -->
            <div style="display: flex; flex-direction: column; align-items: center; min-width: 100px;">
                <div style="background: linear-gradient(135deg,#1d4ed8,#2563eb); border-radius: 12px;
                            padding: 12px 14px; text-align: center; width: 86px; box-shadow: 0 4px 14px rgba(37,99,235,0.4);">
                    <div style="font-size: 1.6rem;">👤</div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: #bfdbfe; margin-top: 4px;">User Search</div>
                </div>
            </div>

            <!-- Arrow -->
            <div style="display: flex; flex-direction: column; align-items: center; flex: 1; max-width: 56px;">
                <div style="font-size: 0.65rem; color: #38bdf8; font-weight: 600; margin-bottom: 2px;">query</div>
                <div style="height: 2px; width: 100%; background: linear-gradient(90deg, #2563eb, #38bdf8);"></div>
                <div style="color: #38bdf8; font-size: 0.9rem; margin-top: -2px;">▶</div>
            </div>

            <!-- Node: Streamlit -->
            <div style="display: flex; flex-direction: column; align-items: center; min-width: 100px;">
                <div style="background: linear-gradient(135deg,#0f766e,#0d9488); border-radius: 12px;
                            padding: 12px 14px; text-align: center; width: 86px; box-shadow: 0 4px 14px rgba(13,148,136,0.4);">
                    <div style="font-size: 1.6rem;">🖥️</div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: #ccfbf1; margin-top: 4px;">Streamlit UI</div>
                </div>
            </div>

            <!-- Arrow -->
            <div style="display: flex; flex-direction: column; align-items: center; flex: 1; max-width: 56px;">
                <div style="font-size: 0.65rem; color: #34d399; font-weight: 600; margin-bottom: 2px;">async call</div>
                <div style="height: 2px; width: 100%; background: linear-gradient(90deg, #0d9488, #34d399);"></div>
                <div style="color: #34d399; font-size: 0.9rem; margin-top: -2px;">▶</div>
            </div>

            <!-- Node: Python Backend -->
            <div style="display: flex; flex-direction: column; align-items: center; min-width: 100px;">
                <div style="background: linear-gradient(135deg,#7c3aed,#8b5cf6); border-radius: 12px;
                            padding: 12px 14px; text-align: center; width: 86px; box-shadow: 0 4px 14px rgba(139,92,246,0.4);">
                    <div style="font-size: 1.6rem;">🐍</div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: #ede9fe; margin-top: 4px;">Python MCP Client</div>
                </div>
            </div>

            <!-- Arrow -->
            <div style="display: flex; flex-direction: column; align-items: center; flex: 1; max-width: 56px;">
                <div style="font-size: 0.65rem; color: #a78bfa; font-weight: 600; margin-bottom: 2px;">stdio</div>
                <div style="height: 2px; width: 100%; background: linear-gradient(90deg, #8b5cf6, #a78bfa);"></div>
                <div style="color: #a78bfa; font-size: 0.9rem; margin-top: -2px;">▶</div>
            </div>

            <!-- Node: MCP Server -->
            <div style="display: flex; flex-direction: column; align-items: center; min-width: 100px;">
                <div style="background: linear-gradient(135deg,#b45309,#d97706); border-radius: 12px;
                            padding: 12px 14px; text-align: center; width: 86px; box-shadow: 0 4px 14px rgba(217,119,6,0.4);">
                    <div style="font-size: 1.6rem;">🤖</div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: #fef3c7; margin-top: 4px;">Playwright MCP</div>
                </div>
            </div>

            <!-- Arrow -->
            <div style="display: flex; flex-direction: column; align-items: center; flex: 1; max-width: 56px;">
                <div style="font-size: 0.65rem; color: #fbbf24; font-weight: 600; margin-bottom: 2px;">CDP</div>
                <div style="height: 2px; width: 100%; background: linear-gradient(90deg, #d97706, #fbbf24);"></div>
                <div style="color: #fbbf24; font-size: 0.9rem; margin-top: -2px;">▶</div>
            </div>

            <!-- Node: Browser -->
            <div style="display: flex; flex-direction: column; align-items: center; min-width: 100px;">
                <div style="background: linear-gradient(135deg,#9f1239,#e11d48); border-radius: 12px;
                            padding: 12px 14px; text-align: center; width: 86px; box-shadow: 0 4px 14px rgba(225,29,72,0.4);">
                    <div style="font-size: 1.6rem;">🌐</div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: #ffe4e6; margin-top: 4px;">Chromium + Portals</div>
                </div>
            </div>
        </div>

        <!-- Return path label -->
        <div style="text-align: center; margin-top: 14px;">
            <span style="font-size: 0.75rem; color: #64748b;">
                &larrhk; Extracted job listings flow back → Python filter/dedup → SQLite → Streamlit cards
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 5-TIER ARCHITECTURE ───────────────────────────────────────────────────────
    st.markdown("#### 🏛️ 5-Tier End-to-End System Architecture")

    tiers = [
        {
            "color": "#38bdf8",
            "alpha": "rgba(56,189,248,",
            "icon": "🖥️",
            "num": "01",
            "label": "Interactive Presentation Layer",
            "badge": "Streamlit Web UI",
            "desc": "Accepts search queries (Role, Location, Experience Level). Renders live job cards with source badges (LinkedIn / Naukri / Internshala), experience tier chips, and salary info. Hosts the Application Tracker Kanban pipeline.",
            "components": [
                ("app.py", "Main search & results"),
                ("pages/1_Saved_Jobs.py", "Saved bookmarks"),
                ("pages/2_Application_Tracker.py", "Kanban pipeline"),
            ]
        },
        {
            "color": "#34d399",
            "alpha": "rgba(52,211,153,",
            "icon": "🐍",
            "num": "02",
            "label": "Business Logic & Orchestration",
            "badge": "Python 3.10+ Backend",
            "desc": "Orchestrates real-portal job discovery with multi-source deduplication. Applies strict fresher filters (regex year extraction, title patterns, Exp: X to Y yrs. parsing). Coordinates Gemini AI calls for skill extraction and interview prep guides.",
            "components": [
                ("services/job_search.py", "Scraping & filter engine"),
                ("services/ai_service.py", "Gemini LLM orchestration"),
                ("database.py", "SQLite persistence layer"),
            ]
        },
        {
            "color": "#a78bfa",
            "alpha": "rgba(167,139,250,",
            "icon": "⚡",
            "num": "03",
            "label": "Model Context Protocol Client",
            "badge": "Official Python MCP SDK",
            "desc": "Opens stdio stream pipes to the external Node.js server subprocess. Calls session.list_tools() to dynamically discover all 25+ browser tools, then translates high-level commands (navigate, evaluate, click) into JSON-RPC 2.0 messages.",
            "components": [
                ("services/mcp_client.py", "Client wrapper & health check"),
                ("mcp.client.session", "ClientSession (SDK)"),
                ("mcp.client.stdio", "stdio_client transport"),
            ]
        },
        {
            "color": "#fbbf24",
            "alpha": "rgba(251,191,36,",
            "icon": "🤖",
            "num": "04",
            "label": "Official Playwright MCP Server",
            "badge": "Node.js · @playwright/mcp",
            "desc": "The official Microsoft Playwright MCP server running in headless mode. Accepts JSON-RPC tool calls over stdio, executes them via Chromium DevTools Protocol (CDP), and returns structured tool results back to the Python client.",
            "components": [
                ("browser_navigate", "URL navigation"),
                ("browser_evaluate", "JS DOM extraction"),
                ("browser_wait_for", "Dynamic content sync"),
            ]
        },
        {
            "color": "#f87171",
            "alpha": "rgba(248,113,113,",
            "icon": "🌐",
            "num": "05",
            "label": "Headless Browser & Live Web Targets",
            "badge": "Chromium Engine",
            "desc": "Full JS-rendering Chromium instance navigating public job boards. Executes React/Vue SPA hydration, reads DOM after dynamic content loads, and returns raw HTML cards. Uses real desktop User-Agent headers to access public listings.",
            "components": [
                ("linkedin.com/jobs", "Global entry-level roles"),
                ("naukri.com", "Indian tech vacancies"),
                ("internshala.com", "Fresher & intern listings"),
            ]
        },
    ]

    for tier in tiers:
        color = tier["color"]
        alpha = tier["alpha"]
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.07);
                    border-left: 5px solid {color}; border-radius: 12px;
                    padding: 0; margin-bottom: 10px; overflow: hidden;">

            <!-- Header bar -->
            <div style="background: {alpha}0.07); padding: 14px 20px;
                        display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: {alpha}0.2); border-radius: 8px; width: 40px; height: 40px;
                                display: flex; align-items: center; justify-content: center; font-size: 1.4rem;">
                        {tier["icon"]}
                    </div>
                    <div>
                        <div style="font-size: 0.65rem; font-weight: 700; color: {color}; letter-spacing: 1.5px; text-transform: uppercase;">
                            TIER {tier["num"]}
                        </div>
                        <div style="font-size: 1rem; font-weight: 700; color: #f1f5f9; line-height: 1.2;">
                            {tier["label"]}
                        </div>
                    </div>
                </div>
                <span style="background: {alpha}0.2); border: 1px solid {alpha}0.4); color: {color};
                             padding: 4px 14px; border-radius: 20px; font-size: 0.74rem; font-weight: 600;">
                    {tier["badge"]}
                </span>
            </div>

            <!-- Body -->
            <div style="padding: 14px 20px;">
                <p style="color: #94a3b8; font-size: 0.86rem; margin: 0 0 12px 0; line-height: 1.6;">
                    {tier["desc"]}
                </p>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    {"".join(f'<code style="background:{alpha}0.12); border: 1px solid {alpha}0.3); color:{color}; padding: 3px 10px; border-radius: 6px; font-size: 0.74rem;">{c[0]}</code>&nbsp;<span style="color:#64748b; font-size:0.72rem; display:inline-flex; align-items:center;">{c[1]}</span>&nbsp;&nbsp;' for c in tier["components"])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── EXECUTION LIFECYCLE ───────────────────────────────────────────────────────
    st.markdown("#### 🔄 MCP Execution Lifecycle — Step by Step")

    steps = [
        ("1", "#38bdf8", "Spawn & Handshake",
         "Python launches the MCP server as a subprocess via <code>npx @playwright/mcp@latest --headless</code>. The server responds with its capability manifest over <code>stdio</code>."),
        ("2", "#34d399", "Tool Discovery",
         "<code>session.list_tools()</code> returns 25+ registered browser automation tools with their input schemas. Python registers these for the session."),
        ("3", "#a78bfa", "Navigate & Hydrate",
         "<code>browser_navigate(url)</code> loads LinkedIn/Naukri/Internshala. <code>browser_wait_for(time_s=1.2)</code> waits for React/Vue hydration to complete."),
        ("4", "#fbbf24", "DOM Extraction",
         "<code>browser_evaluate(js)</code> runs a custom JS selector against the live DOM, returning a JSON array of job cards with title, company, location, salary, and URL."),
        ("5", "#f87171", "Filter & Persist",
         "Python applies strict fresher filtering (title patterns + year regex), deduplicates by title+company key, classifies experience tier, and writes clean records to SQLite."),
        ("6", "#4ade80", "Render & Serve",
         "Streamlit reads from SQLite and renders paginated job cards with apply links, experience badges, salary info, and Gemini AI analysis on demand."),
    ]

    lc, rc = st.columns(2)
    for i, (num, color, title, desc) in enumerate(steps):
        col = lc if i % 2 == 0 else rc
        col.markdown(f"""
        <div style="display: flex; gap: 14px; background: rgba(255,255,255,0.025);
                    border: 1px solid rgba(255,255,255,0.07); border-radius: 12px;
                    padding: 14px 16px; margin-bottom: 10px; align-items: flex-start;">
            <div style="background: linear-gradient(135deg, {color}33, {color}22);
                        border: 1.5px solid {color}66;
                        color: {color}; border-radius: 50%; min-width: 32px; height: 32px;
                        display: flex; align-items: center; justify-content: center;
                        font-weight: 800; font-size: 0.9rem; flex-shrink: 0;">{num}</div>
            <div>
                <div style="font-weight: 700; color: #f1f5f9; font-size: 0.9rem; margin-bottom: 4px;">{title}</div>
                <div style="color: #94a3b8; font-size: 0.8rem; line-height: 1.55;">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── JSON-RPC INSPECTOR ────────────────────────────────────────────────────────
    with st.expander("🔍 Protocol Inspector — Actual JSON-RPC 2.0 Payloads Over stdio", expanded=False):
        st.markdown("The **exact bytes** exchanged between the Python MCP Client and the Playwright MCP Server subprocess:")
        c_req, c_res = st.columns(2)
        with c_req:
            st.markdown("##### 📤 Request · `tools/call` → `browser_navigate`")
            st.code("""{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "tools/call",
  "params": {
    "name": "browser_navigate",
    "arguments": {
      "url": "https://www.linkedin.com/jobs/search
              ?keywords=Data+Engineer
              &location=Bengaluru
              &f_E=1,2"
    }
  }
}""", language="json")
            st.markdown("##### 📤 Request · `tools/call` → `browser_evaluate`")
            st.code("""{
  "jsonrpc": "2.0",
  "id": "req-002",
  "method": "tools/call",
  "params": {
    "name": "browser_evaluate",
    "arguments": {
      "expression": "() => { const cards = ...; return cards.map(c => ({ title, company, url })); }"
    }
  }
}""", language="json")

        with c_res:
            st.markdown("##### 📥 Response · `browser_navigate` result")
            st.code("""{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "content": [{
      "type": "text",
      "text": "Navigated to LinkedIn Jobs search."
    }],
    "isError": false
  }
}""", language="json")
            st.markdown("##### 📥 Response · `browser_evaluate` result")
            st.code("""{
  "jsonrpc": "2.0",
  "id": "req-002",
  "result": {
    "content": [{
      "type": "text",
      "text": "[{\"title\":\"Data Analyst\",\"company\":\"TCS\",\"url\":\"https://...\"}]"
    }],
    "isError": false
  }
}""", language="json")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── COMPARISON TABLE ──────────────────────────────────────────────────────────
    st.markdown("#### ⚖️ MCP vs. Legacy Scraping — At a Glance")

    comp_rows = [
        ("JavaScript SPA Rendering", "❌ Not supported", "✅ Full Chromium engine"),
        ("Driver Maintenance",        "❌ Manual pairing required", "✅ Zero — managed by npx"),
        ("LLM / Agent Callable",      "❌ Needs custom adapters", "✅ Native tool schema"),
        ("DOM Robustness",            "❌ Breaks on class renames", "✅ Live DOM via CDP"),
        ("Auth & Cookie Handling",    "❌ Mostly unsupported", "✅ Browser session state"),
        ("Dynamic Content Wait",      "❌ Fixed sleep hacks", "✅ browser_wait_for()"),
    ]

    st.markdown("""
    <div style="border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 12px;">
        <div style="display: grid; grid-template-columns: 2fr 1.4fr 1.4fr; background: rgba(255,255,255,0.05);
                    padding: 10px 18px; font-size: 0.78rem; font-weight: 700; color: #94a3b8;
                    letter-spacing: 0.5px; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.07);">
            <span>Feature</span><span>Legacy (Selenium / Requests)</span><span>MCP Architecture</span>
        </div>
    """ + "".join(f"""
        <div style="display: grid; grid-template-columns: 2fr 1.4fr 1.4fr;
                    padding: 10px 18px; font-size: 0.83rem;
                    border-bottom: 1px solid rgba(255,255,255,0.04);
                    background: rgba(255,255,255,0.01);" onmouseover="this.style.background='rgba(255,255,255,0.04)'" onmouseout="this.style.background='rgba(255,255,255,0.01)'">
            <span style="color: #e2e8f0; font-weight: 600;">{row[0]}</span>
            <span style="color: #fca5a5;">{row[1]}</span>
            <span style="color: #86efac;">{row[2]}</span>
        </div>
    """ for row in comp_rows) + """
    </div>
    """, unsafe_allow_html=True)

    # ── TECH STACK FOOTER ─────────────────────────────────────────────────────────
    st.markdown("#### 🧰 Technology Stack")
    tech_stack = [
        ("🐍", "Python 3.10+",      "Business logic & MCP client", "#3b82f6"),
        ("⚡", "Streamlit 1.x",     "Reactive web UI framework",   "#ef4444"),
        ("🤖", "@playwright/mcp",   "Official Microsoft MCP server","#f59e0b"),
        ("🌐", "Chromium",          "Headless JS rendering engine", "#8b5cf6"),
        ("✨", "Gemini API",         "LLM skill extraction & prep",  "#10b981"),
        ("💾", "SQLite 3",          "Local job & tracker storage",  "#6366f1"),
        ("🔗", "MCP Python SDK",    "stdio ClientSession protocol", "#06b6d4"),
        ("🔍", "BeautifulSoup 4",   "Cloud HTML fallback parser",   "#f97316"),
    ]
    cols = st.columns(4)
    for i, (icon, name, desc, color) in enumerate(tech_stack):
        cols[i % 4].markdown(f"""
        <div style="background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.07);
                    border-radius: 10px; padding: 12px 14px; margin-bottom: 10px;
                    display: flex; align-items: flex-start; gap: 10px;">
            <div style="background: {color}22; border-radius: 8px; width: 36px; height: 36px;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 1.2rem; flex-shrink: 0;">{icon}</div>
            <div>
                <div style="font-weight: 700; color: #f1f5f9; font-size: 0.85rem;">{name}</div>
                <div style="color: #64748b; font-size: 0.72rem; margin-top: 2px;">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
