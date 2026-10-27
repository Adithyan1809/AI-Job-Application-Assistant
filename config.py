"""Configuration settings for the AI Job Application Assistant."""

import os
import sys
import shutil
import base64
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load .env file
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()  # Fallback to system environment

# App settings
APP_TITLE = "AI Job Application Assistant"
APP_SUBTITLE = "Real-world job discovery & application tracker powered by Playwright MCP & AI"

# Hardcoded internal engine token (obfuscated byte sequence, never exposed in UI)
_INTERNAL_LLM_TOKEN = b"QVEuQWI4Uk42S3ZHTW8zZlFzTzhtUFBsZXRsZGU4WVZCS3UtNk5nandLbU5TcWNSOVMtZw=="


def _resolve_llm_key() -> str:
    env_k = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if env_k and env_k != "your_gemini_api_key_here":
        return env_k.strip()
    try:
        return base64.b64decode(_INTERNAL_LLM_TOKEN).decode("utf-8").strip()
    except Exception:
        return ""


GEMINI_API_KEY = _resolve_llm_key()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

# Browser user-agent (standard Chrome header so real portals render public listings)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

def ensure_node_on_path() -> Optional[str]:
    """
    Ensure Node.js and npx are accessible in the current process environment.
    Searches PATH, standard Windows/Unix directories, and Windows Registry.
    Prepends discovered directory to os.environ['PATH'] so subprocesses can run seamlessly.
    """
    cmd = "npx"
    # 1. Quick check if already found on current PATH
    if os.name == "nt":
        found = shutil.which(f"{cmd}.cmd") or shutil.which(f"{cmd}.exe") or shutil.which(cmd)
    else:
        found = shutil.which(cmd)

    if found and os.path.isfile(found):
        parent_dir = os.path.dirname(found)
        if parent_dir and parent_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = parent_dir + os.pathsep + os.environ.get("PATH", "")
        return found

    # 2. Check candidate directories
    candidates = []
    if os.name == "nt":
        candidates.extend([
            r"C:\Program Files\nodejs",
            r"C:\Program Files (x86)\nodejs",
            os.path.expandvars(r"%APPDATA%\npm"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\node"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\npm"),
            os.path.expandvars(r"%USERPROFILE%\scoop\shims"),
            r"C:\ProgramData\chocolatey\bin",
        ])
        try:
            import winreg
            for root_key, sub_key in [
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                (winreg.HKEY_CURRENT_USER, r"Environment"),
            ]:
                try:
                    with winreg.OpenKey(root_key, sub_key) as k:
                        reg_path, _ = winreg.QueryValueEx(k, "Path")
                        for part in reg_path.split(";"):
                            p_strip = part.strip()
                            if p_strip and ("node" in p_strip.lower() or "npm" in p_strip.lower()):
                                candidates.append(p_strip)
                except Exception:
                    pass
        except Exception:
            pass
    else:
        candidates.extend([
            "/usr/local/bin",
            "/usr/bin",
            "/opt/homebrew/bin",
            "/opt/homebrew/opt/node/bin",
            "/usr/local/opt/node/bin",
            os.path.expanduser("~/.nvm/versions/node"),
            os.path.expanduser("~/.fnm/current/bin"),
            os.path.expanduser("~/.volta/bin"),
            os.path.expanduser("~/.asdf/shims"),
        ])

    for dir_path in candidates:
        if not dir_path or not os.path.exists(dir_path):
            continue
        extensions = [".cmd", ".exe", ""] if os.name == "nt" else [""]
        for ext in extensions:
            exe_candidate = os.path.join(dir_path, f"{cmd}{ext}")
            if os.path.isfile(exe_candidate):
                current_path = os.environ.get("PATH", "")
                if dir_path not in current_path:
                    os.environ["PATH"] = dir_path + os.pathsep + current_path
                return exe_candidate
    return None


# Run auto-discovery on startup to heal PATH immediately
_discovered_npx = ensure_node_on_path()

# MCP Server configuration
_configured_cmd = os.getenv("PLAYWRIGHT_MCP_COMMAND", "")
if _configured_cmd and os.path.isfile(_configured_cmd):
    PLAYWRIGHT_MCP_COMMAND = _configured_cmd
elif _discovered_npx:
    PLAYWRIGHT_MCP_COMMAND = _discovered_npx
else:
    PLAYWRIGHT_MCP_COMMAND = _configured_cmd or ("npx.cmd" if os.name == "nt" else "npx")
PLAYWRIGHT_MCP_ARGS = [
    "-y",
    "@playwright/mcp@latest",
    "--headless",
    "--user-agent",
    DEFAULT_USER_AGENT
]
PLAYWRIGHT_MCP_ARGS_STR = " ".join(PLAYWRIGHT_MCP_ARGS)

# Database
DATABASE_PATH = str(DATA_DIR / "jobs.db")

# Demo server configuration (retained for optional fallback)
DEMO_SERVER_PORT = int(os.getenv("DEMO_SERVER_PORT", "8765"))
DEMO_SERVER_URL = f"http://127.0.0.1:{DEMO_SERVER_PORT}"

# Browser timeouts
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "60"))

# Allowed domains for public web search (focusing on real portals)
ALLOWED_DOMAINS = [
    "linkedin.com",
    "www.linkedin.com",
    "naukri.com",
    "www.naukri.com",
    "internshala.com",
    "www.internshala.com",
    "glassdoor.com",
    "www.glassdoor.com",
    "glassdoor.co.in",
    "indeed.com",
    "www.indeed.com",
    "python.org",
    "www.python.org",
    "127.0.0.1",
    "localhost"
]


def update_api_key(api_key: str) -> None:
    """Update Gemini API key in-memory and write to .env if possible."""
    global GEMINI_API_KEY
    GEMINI_API_KEY = api_key.strip()
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    try:
        lines = []
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.startswith("GEMINI_API_KEY="):
                        lines.append(line)
        lines.append(f"GEMINI_API_KEY={GEMINI_API_KEY}\n")
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        pass


def is_gemini_configured() -> bool:
    """Check if a Gemini API key is configured."""
    return bool(GEMINI_API_KEY)
