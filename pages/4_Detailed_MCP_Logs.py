"""Page 4: Detailed Model Context Protocol (MCP) Logs & Protocol Inspector."""

import json
import asyncio
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any

from config import (
    APP_TITLE,
    PLAYWRIGHT_MCP_COMMAND,
    PLAYWRIGHT_MCP_ARGS_STR
)
from database import (
    init_db,
    get_mcp_logs,
    clear_mcp_logs,
    get_mcp_log_stats,
    log_mcp_event
)
from services.mcp_client import PlaywrightMCPClient, check_mcp_health

init_db()

st.set_page_config(
    page_title=f"Detailed MCP Logs - {APP_TITLE}",
    page_icon="📋",
    layout="wide"
)

def render_html(html_code: str, container=st):
    """Safely render raw HTML directly via st.html without Markdown parser interference."""
    clean = "\n".join(line.strip() for line in html_code.strip().splitlines() if line.strip())
    if hasattr(container, "html"):
        container.html(clean)
    else:
        container.markdown(clean, unsafe_allow_html=True)


# Seed initial diagnostic log if database has 0 logs
stats = get_mcp_log_stats()
if stats["total"] == 0:
    log_mcp_event(
        event_type="SYSTEM_BOOT",
        tool_name="mcp_subsystem",
        arguments={"executable": PLAYWRIGHT_MCP_COMMAND, "args": PLAYWRIGHT_MCP_ARGS_STR},
        response="Playwright MCP logging subsystem initialized and listening on stdio.",
        status="INFO"
    )
    stats = get_mcp_log_stats()

# Header Section
st.title("📋 Detailed Model Context Protocol (MCP) Logs")
st.markdown("Live inspect JSON-RPC 2.0 messages, tool execution latency, browser automation lifecycle, and `stdio` diagnostics.")

# Top Metric KPI Cards
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total MCP Operations", f"{stats['total']:,}")
m2.metric("Success Rate", f"{stats['success_rate']}%")
m3.metric("Average Tool Latency", f"{stats['avg_duration_ms']} ms")
m4.metric("Discovered Tools", f"{len(stats['tools_seen'])} tools")

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Action Toolbar
c_act1, c_act2, c_act3, c_act4 = st.columns([1.2, 1.8, 1.2, 1.2])
with c_act1:
    if st.button("🔄 Refresh Logs", use_container_width=True):
        st.rerun()

with c_act2:
    if st.button("🧪 Ping Playwright MCP Server", type="primary", use_container_width=True):
        with st.spinner("Connecting to Playwright MCP server over stdio..."):
            healthy, msg, tools = check_mcp_health()
            if healthy:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")
            st.rerun()

with c_act3:
    if st.button("🧹 Clear All Logs", use_container_width=True):
        clear_mcp_logs()
        st.success("All MCP execution logs cleared!")
        st.rerun()

with c_act4:
    all_current_logs = get_mcp_logs(limit=500)
    if all_current_logs:
        json_data = json.dumps(all_current_logs, indent=2)
        st.download_button(
            label="📥 Export JSON",
            data=json_data,
            file_name=f"mcp_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.button("📥 Export JSON", disabled=True, use_container_width=True)

st.markdown("---")

# Interactive MCP Tool Execution Playground
with st.expander("🧪 Interactive Live MCP Tool Playground", expanded=False):
    st.markdown("Test calling any official Playwright MCP tool directly over `stdio` and inspect the resulting JSON-RPC 2.0 message:")
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        test_tool = st.selectbox(
            "Select MCP Tool to Test",
            ["list_tools", "browser_navigate", "browser_evaluate", "browser_snapshot", "browser_wait_for"]
        )
    with col_t2:
        test_args: Dict[str, Any] = {}
        if test_tool == "list_tools":
            st.info("Discovers all 25+ browser automation tools registered by the MCP server.")
        elif test_tool == "browser_navigate":
            target_url = st.text_input("Target URL", value="https://www.linkedin.com/jobs/search?keywords=Data+Engineer&location=Bengaluru")
            test_args = {"url": target_url}
        elif test_tool == "browser_evaluate":
            js_code = st.text_input("JavaScript Expression", value="() => ({ pageTitle: document.title, url: window.location.href })")
            test_args = {"function": js_code}
        elif test_tool == "browser_snapshot":
            depth = st.number_input("Max DOM Snapshot Depth", min_value=1, max_value=20, value=5)
            test_args = {"depth": depth}
        elif test_tool == "browser_wait_for":
            wait_s = st.slider("Wait Duration (seconds)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
            test_args = {"time": wait_s}

    if st.button("🚀 Execute Tool Call via MCP", type="primary"):
        with st.spinner(f"Executing {test_tool} on Playwright MCP server..."):
            try:
                async def _run_tool():
                    async with PlaywrightMCPClient() as client:
                        if test_tool == "list_tools":
                            tools = await client.list_available_tools()
                            return {"tools_count": len(tools), "tools": tools}
                        elif test_tool == "browser_navigate":
                            return await client.navigate(test_args["url"])
                        elif test_tool == "browser_evaluate":
                            return await client.evaluate(test_args["function"])
                        elif test_tool == "browser_snapshot":
                            return await client.take_snapshot(test_args.get("depth", 5))
                        elif test_tool == "browser_wait_for":
                            return await client.wait_for(time_s=test_args.get("time", 1.0))

                try:
                    res = asyncio.run(_run_tool())
                except RuntimeError:
                    import nest_asyncio
                    nest_asyncio.apply()
                    res = asyncio.get_event_loop().run_until_complete(_run_tool())

                st.success(f"✅ Tool `{test_tool}` executed successfully!")
                st.json(res if isinstance(res, (dict, list)) else {"raw_response": str(res)})
                st.rerun()
            except Exception as ex:
                st.error(f"❌ Tool execution failed: {ex}")

# Filter Bar
st.markdown("### 🔍 Filter & Search MCP Logs")
f1, f2, f3, f4, f5 = st.columns([1.5, 1.2, 1.2, 1.0, 0.8])
with f1:
    search_term = st.text_input("Search Logs", placeholder="Search by URL, tool, error, arguments...", label_visibility="collapsed")
with f2:
    event_filter = st.selectbox("Event Type", ["All", "TOOL_RESULT", "TOOL_CALL", "TOOL_DISCOVERY", "SESSION_START", "SESSION_CLOSE", "SESSION_ERROR", "FALLBACK_DIRECT", "SYSTEM_BOOT"])
with f3:
    candidate_tools = sorted(list(set(stats.get("tools_seen", []) + ["browser_navigate", "browser_evaluate", "browser_wait_for", "list_tools", "client.connect"])))
    tool_filter = st.selectbox("Tool Name", ["All"] + candidate_tools)
with f4:
    status_filter = st.selectbox("Status", ["All", "SUCCESS", "ERROR", "INFO", "WARNING"])
with f5:
    limit_count = st.selectbox("Limit", [50, 100, 200, 500], index=1)

# Retrieve filtered logs
logs = get_mcp_logs(
    limit=limit_count,
    event_type=event_filter,
    tool_name=tool_filter,
    status=status_filter,
    search=search_term
)

st.markdown(f"**Showing {len(logs)} MCP Log Entries** (Latest first)")

# Display Tabs
tab_cards, tab_table, tab_stream = st.tabs([
    "📜 Detailed Protocol Cards",
    "📊 Tabular Log View",
    "💻 Terminal Stream"
])

# TAB 1: Detailed Protocol Cards
with tab_cards:
    if not logs:
        st.info("💡 No MCP logs found matching your filter criteria. Try broadening your search or click **Ping Playwright MCP Server** above.")
    else:
        for item in logs:
            status = item.get("status", "SUCCESS")
            duration = item.get("duration_ms", 0.0)
            event_type = item.get("event_type", "TOOL_RESULT")
            tool_name = item.get("tool_name", "generic_call")
            timestamp = item.get("timestamp", "")
            err = item.get("error_message") or ""

            # Theme colors
            if status == "SUCCESS":
                border_color = "#10b981"
                status_badge = "🟢 SUCCESS"
                bg_badge = "rgba(16, 185, 129, 0.15)"
            elif status == "ERROR":
                border_color = "#ef4444"
                status_badge = "🔴 ERROR"
                bg_badge = "rgba(239, 68, 68, 0.15)"
            elif status == "WARNING":
                border_color = "#f59e0b"
                status_badge = "🟡 WARNING"
                bg_badge = "rgba(245, 158, 11, 0.15)"
            else:
                border_color = "#3b82f6"
                status_badge = "🔵 INFO"
                bg_badge = "rgba(59, 130, 246, 0.15)"

            # Parse arguments
            args_obj = {}
            if item.get("arguments"):
                try:
                    args_obj = json.loads(item["arguments"])
                except Exception:
                    args_obj = {"raw": item["arguments"]}

            # Parse response
            resp_full = item.get("response_full") or item.get("response") or ""
            resp_obj = None
            if resp_full:
                try:
                    resp_obj = json.loads(resp_full)
                except Exception:
                    resp_obj = resp_full

            # Render summary card
            render_html(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08);
                        border-left: 5px solid {border_color}; border-radius: 10px;
                        padding: 12px 18px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="background: {bg_badge}; color: {border_color}; font-size: 0.74rem; font-weight: 700;
                                     padding: 3px 10px; border-radius: 12px; border: 1px solid {border_color}44;">
                            {status_badge}
                        </span>
                        <code style="color: #60a5fa; font-size: 0.88rem; font-weight: 700;">{tool_name}</code>
                        <span style="color: #94a3b8; font-size: 0.78rem;">[{event_type}]</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="color: #cbd5e1; font-size: 0.76rem; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 6px;">
                            ⚡ {duration} ms
                        </span>
                        <span style="color: #64748b; font-size: 0.76rem;">
                            ⏱️ {timestamp}
                        </span>
                    </div>
                </div>
            </div>
            """)

            with st.expander(f"🔍 Inspect JSON-RPC 2.0 Payload · Log #{item.get('id', 0)} ({tool_name})", expanded=False):
                col_req, col_res = st.columns(2)
                with col_req:
                    st.markdown("##### 📤 Request: `tools/call` over stdio")
                    req_payload = {
                        "jsonrpc": "2.0",
                        "id": f"req-{item.get('id', 0)}",
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": args_obj
                        }
                    }
                    st.code(json.dumps(req_payload, indent=2), language="json")

                with col_res:
                    st.markdown("##### 📥 Response: Tool Output")
                    if status == "ERROR":
                        err_payload = {
                            "jsonrpc": "2.0",
                            "id": f"req-{item.get('id', 0)}",
                            "error": {
                                "code": -32603,
                                "message": err
                            }
                        }
                        st.code(json.dumps(err_payload, indent=2), language="json")
                        st.error(f"Error: {err}")
                    else:
                        res_payload = {
                            "jsonrpc": "2.0",
                            "id": f"req-{item.get('id', 0)}",
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": resp_obj if isinstance(resp_obj, str) else json.dumps(resp_obj)
                                    }
                                ],
                                "isError": False
                            }
                        }
                        st.code(json.dumps(res_payload, indent=2), language="json")

# TAB 2: Tabular Log View
with tab_table:
    if not logs:
        st.info("No logs available for tabular display.")
    else:
        df_logs = pd.DataFrame(logs)
        display_cols = ["id", "timestamp", "event_type", "tool_name", "status", "duration_ms", "arguments", "response", "error_message"]
        available_cols = [c for c in display_cols if c in df_logs.columns]
        st.dataframe(
            df_logs[available_cols],
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
                "event_type": st.column_config.TextColumn("Event Type", width="small"),
                "tool_name": st.column_config.TextColumn("Tool Name", width="medium"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "duration_ms": st.column_config.NumberColumn("Duration (ms)", format="%.1f ms", width="small"),
                "arguments": st.column_config.TextColumn("Arguments", width="large"),
                "response": st.column_config.TextColumn("Response Preview", width="large"),
                "error_message": st.column_config.TextColumn("Error", width="medium"),
            },
            hide_index=True
        )

# TAB 3: Terminal Stream
with tab_stream:
    st.markdown("#### 💻 Real-Time Stdio Log Stream")
    if not logs:
        st.caption("No stream logs recorded.")
    else:
        terminal_lines = []
        for l in reversed(logs):
            t = l.get("timestamp", "")
            ev = l.get("event_type", "TOOL")
            tl = l.get("tool_name", "mcp")
            st_val = l.get("status", "OK")
            dur = l.get("duration_ms", 0.0)
            args_snip = l.get("arguments", "")[:60]
            if args_snip:
                args_snip = f" args={args_snip}"
            err_snip = f" ERR: {l.get('error_message')}" if l.get("error_message") else ""
            line = f"[{t}] [{ev}] [{tl}] status={st_val} ({dur}ms){args_snip}{err_snip}"
            terminal_lines.append(line)

        terminal_text = "\n".join(terminal_lines)
        st.text_area(
            "Stdio Stream Output",
            value=terminal_text,
            height=400,
            disabled=True,
            label_visibility="collapsed"
        )
