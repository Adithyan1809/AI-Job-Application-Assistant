"""Playwright MCP Client integration using the official Model Context Protocol (MCP) Python SDK."""

import os
import sys
import shutil
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from config import PLAYWRIGHT_MCP_COMMAND, PLAYWRIGHT_MCP_ARGS, BROWSER_TIMEOUT, ensure_node_on_path
from database import log_mcp_event


class MCPConnectionError(Exception):
    """Raised when connecting to or communicating with the Playwright MCP server fails."""
    pass


class PlaywrightMCPClient:
    """
    Manages an MCP client session communicating with the official Playwright MCP server over stdio.
    
    Architecture:
    Python App -> mcp.client.session.ClientSession -> StdioTransport -> npx @playwright/mcp -> Headless Browser
    """

    def __init__(
        self,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        timeout: int = BROWSER_TIMEOUT
    ):
        self.command = command or PLAYWRIGHT_MCP_COMMAND
        self.args = args or PLAYWRIGHT_MCP_ARGS
        self.timeout = timeout
        self._session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._stdio_ctx = None
        self._session_ctx = None
        self._available_tools: List[str] = []

    def _resolve_executable(self) -> str:
        """Resolve command executable on Windows or POSIX, auto-healing PATH if needed."""
        ensure_node_on_path()
        cmd = self.command

        # If cmd is directly a valid file path, return it
        if os.path.isfile(cmd):
            return cmd

        if os.name == "nt":
            if not cmd.lower().endswith((".cmd", ".exe", ".bat")):
                # Check for cmd variant first (common for npm/npx on Windows)
                cmd_with_ext = shutil.which(f"{cmd}.cmd")
                if cmd_with_ext:
                    return cmd_with_ext
                cmd_with_exe = shutil.which(f"{cmd}.exe")
                if cmd_with_exe:
                    return cmd_with_exe

        resolved = shutil.which(cmd)
        if resolved:
            return resolved

        # Fallback check using discovered npx
        auto_npx = ensure_node_on_path()
        if auto_npx and cmd in ("npx", "npx.cmd"):
            return auto_npx

        return cmd

    async def __aenter__(self) -> "PlaywrightMCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def connect(self) -> None:
        """Establish stdio connection and initialize MCP session with Playwright server."""
        executable = self._resolve_executable()
        t0 = time.perf_counter()
        
        # Verify npx / node executable
        if not os.path.isfile(executable) and not shutil.which(executable) and not shutil.which(self.command):
            err_msg = (
                f"Could not find executable '{self.command}' or '{executable}' on system PATH. "
                "Please verify that Node.js and npm are installed (visit https://nodejs.org or run 'winget install OpenJS.NodeJS')."
            )
            log_mcp_event(
                event_type="SESSION_ERROR",
                tool_name="client.connect",
                arguments={"command": self.command, "resolved": executable},
                error_message=err_msg,
                duration_ms=0.0,
                status="ERROR"
            )
            raise MCPConnectionError(err_msg)

        log_mcp_event(
            event_type="SESSION_START",
            tool_name="client.connect",
            arguments={"command": executable, "args": self.args},
            status="INFO"
        )

        env = dict(os.environ)
        # Ensure utf-8 encoding for stdio
        env["PYTHONIOENCODING"] = "utf-8"
        # Ensure parent directory of executable is in env['PATH']
        exe_dir = os.path.dirname(executable)
        if exe_dir and exe_dir not in env.get("PATH", ""):
            env["PATH"] = exe_dir + os.pathsep + env.get("PATH", "")

        server_params = StdioServerParameters(
            command=executable,
            args=self.args,
            env=env,
        )

        try:
            self._stdio_ctx = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._stdio_ctx.__aenter__()

            self._session_ctx = ClientSession(self._read_stream, self._write_stream)
            self._session = await self._session_ctx.__aenter__()

            # Initialize session
            init_result = await asyncio.wait_for(
                self._session.initialize(),
                timeout=self.timeout
            )
            
            # Cache tool names
            tools_resp = await self._session.list_tools()
            self._available_tools = [t.name for t in tools_resp.tools]

            dur = (time.perf_counter() - t0) * 1000.0
            log_mcp_event(
                event_type="TOOL_DISCOVERY",
                tool_name="list_tools",
                arguments={"timeout": self.timeout},
                response={"tools_count": len(self._available_tools), "tools": self._available_tools},
                duration_ms=dur,
                status="SUCCESS"
            )

        except asyncio.TimeoutError:
            await self.close()
            dur = (time.perf_counter() - t0) * 1000.0
            err_msg = (
                f"Connection to Playwright MCP timed out after {self.timeout}s. "
                "First-time package download through npx may require more time or an active network."
            )
            log_mcp_event(
                event_type="SESSION_ERROR",
                tool_name="client.connect",
                arguments={"command": executable},
                error_message=err_msg,
                duration_ms=dur,
                status="ERROR"
            )
            raise MCPConnectionError(err_msg)
        except Exception as e:
            await self.close()
            dur = (time.perf_counter() - t0) * 1000.0
            err_msg = f"Failed to initialize Playwright MCP session: {e}"
            log_mcp_event(
                event_type="SESSION_ERROR",
                tool_name="client.connect",
                arguments={"command": executable},
                error_message=err_msg,
                duration_ms=dur,
                status="ERROR"
            )
            raise MCPConnectionError(err_msg) from e

    async def close(self) -> None:
        """Gracefully terminate session and streams."""
        if self._session_ctx:
            try:
                await self._session_ctx.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_ctx = None
            self._session = None

        if self._stdio_ctx:
            try:
                await self._stdio_ctx.__aexit__(None, None, None)
            except Exception:
                pass
            self._stdio_ctx = None
            self._read_stream = None
            self._write_stream = None

        log_mcp_event(
            event_type="SESSION_CLOSE",
            tool_name="client.close",
            status="INFO"
        )

    def _ensure_connected(self) -> ClientSession:
        if not self._session:
            raise MCPConnectionError("MCP Client is not connected. Call connect() first.")
        return self._session

    async def list_available_tools(self) -> List[str]:
        """Return cached list of tool names provided by the Playwright MCP server."""
        if not self._available_tools and self._session:
            tools_resp = await self._session.list_tools()
            self._available_tools = [t.name for t in tools_resp.tools]
        return self._available_tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call any generic tool on the Playwright MCP server and extract text response."""
        session = self._ensure_connected()
        t0 = time.perf_counter()
        try:
            result = await session.call_tool(name, arguments=arguments)
            dur = (time.perf_counter() - t0) * 1000.0
            
            texts = []
            for c in result.content:
                if hasattr(c, "text") and c.text:
                    texts.append(c.text)
            resp_text = "\n".join(texts)

            log_mcp_event(
                event_type="TOOL_RESULT",
                tool_name=name,
                arguments=arguments,
                response=resp_text,
                duration_ms=dur,
                status="SUCCESS"
            )
            return resp_text
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000.0
            log_mcp_event(
                event_type="TOOL_ERROR",
                tool_name=name,
                arguments=arguments,
                error_message=str(e),
                duration_ms=dur,
                status="ERROR"
            )
            raise

    async def navigate(self, url: str) -> str:
        """
        Navigate browser to target URL via MCP 'browser_navigate' tool.
        """
        return await self.call_tool("browser_navigate", {"url": url})

    async def take_snapshot(self, depth: Optional[int] = None) -> str:
        """
        Capture accessibility tree snapshot via MCP 'browser_snapshot' tool.
        """
        args: Dict[str, Any] = {}
        if depth:
            args["depth"] = depth
        return await self.call_tool("browser_snapshot", args)

    async def fill_field(self, target: str, value: str, name: str = "field", field_type: str = "textbox") -> str:
        """
        Fill a form field via MCP 'browser_fill_form' tool.
        """
        fields = [{
            "target": target,
            "name": name,
            "type": field_type,
            "value": str(value)
        }]
        return await self.call_tool("browser_fill_form", {"fields": fields})

    async def type_text(self, target: str, text: str, submit: bool = False) -> str:
        """
        Type text into an editable element via MCP 'browser_type' tool.
        """
        return await self.call_tool("browser_type", {
            "target": target,
            "text": text,
            "submit": submit
        })

    async def click(self, target: str) -> str:
        """
        Click an element via MCP 'browser_click' tool.
        """
        return await self.call_tool("browser_click", {"target": target})

    async def wait_for(self, text: Optional[str] = None, time_s: Optional[float] = None, time_ms: Optional[int] = None) -> str:
        """
        Wait for text or time duration (in seconds) via MCP 'browser_wait_for' tool.
        """
        args: Dict[str, Any] = {}
        if text:
            args["text"] = text
        if time_s is not None:
            args["time"] = float(time_s)
        elif time_ms is not None:
            args["time"] = max(float(time_ms) / 1000.0, 0.5)
        return await self.call_tool("browser_wait_for", args)

    async def evaluate(self, js_function: str) -> str:
        """
        Evaluate JavaScript in browser context via MCP 'browser_evaluate' tool.
        """
        return await self.call_tool("browser_evaluate", {"function": js_function})


async def async_check_mcp_health() -> Tuple[bool, str, List[str]]:
    """
    Perform a health check on the Playwright MCP server.
    Returns (healthy: bool, message: str, available_tools: List[str]).
    """
    client = PlaywrightMCPClient()
    try:
        async with client:
            tools = await client.list_available_tools()
            return True, f"Successfully connected to Playwright MCP! Server exposes {len(tools)} tools.", tools
    except Exception as e:
        return False, f"Playwright MCP connection failed: {e}", []


def check_mcp_health() -> Tuple[bool, str, List[str]]:
    """Synchronous entry point for health check."""
    try:
        return asyncio.run(async_check_mcp_health())
    except RuntimeError:
        try:
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_check_mcp_health())
        except Exception as e:
            return False, f"Playwright MCP health check failed: {e}", []
    except Exception as e:
        return False, f"Playwright MCP check error: {e}", []
