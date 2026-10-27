# 💼 AI Job Application Assistant using Playwright MCP

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright MCP](https://img.shields.io/badge/Playwright-MCP-2EAD33.svg)](https://playwright.dev/mcp/introduction)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An AI-powered job discovery and application tracking web application designed for students and freshers. The project demonstrates how the **Model Context Protocol (MCP)** and **Playwright** empower AI applications to automate browser interactions, inspect live web pages, extract structured career opportunities, and track applications.

---

## 📌 Project Objectives

1. **Practical Demonstration of Playwright MCP:** Showcases how Python communicates with the official Playwright MCP server over `stdio` via JSON-RPC to automate browser actions (`browser_navigate`, `browser_wait_for`, `browser_snapshot`, `browser_type`, `browser_click`, `browser_evaluate`).
2. **Real Job Portal Scraping:** Genuinely scrapes public job openings from **LinkedIn Jobs**, **Naukri.com**, and **Internshala** directly using Playwright MCP tools.
3. **Student & Fresher Career Discovery:** Discovers entry-level, internship, and early-career opportunities, filters roles, and provides actionable interview preparation tips.
4. **Application Tracking Pipeline:** Maintains application statuses (`Interested`, `Applied`, `Interview`, `Offer`, `Rejected`) in an SQLite database with duplicate prevention and timeline notes.

---

## 🏛️ System Architecture

```
User (Browser)
      │
      ▼
Streamlit Frontend (app.py & pages/)
      │
      ▼
Python Backend (services/job_search.py, services/ai_service.py)
      │
      ▼  (JSON-RPC via stdio using Python MCP SDK)
Official Playwright MCP Server (`npx -y @playwright/mcp@latest --headless --user-agent ...`)
      │
      ▼  (Chrome DevTools Protocol)
Headless Chromium Browser
      │
      ▼
Real Job Portals: LinkedIn Jobs / Naukri.com / Internshala
      │
      ▼  (DOM Evaluation & Extraction via Playwright MCP tools)
Structured Job Opportunities
      │
      ▼
SQLite Database (`data/jobs.db`) & Streamlit UI (Cards, Filters, Tracker)
```

---

## 🌟 Key Features

| Feature | Description |
| :--- | :--- |
| **🔍 Job Search Dashboard** | Search by role, preferred location, experience (Fresher, Internship, 0–1 yrs, 1–2 yrs), employment type, and salary. |
| **🤖 Playwright MCP Automation** | True MCP integration invoking standardized tools (`browser_navigate`, `browser_type`, `browser_click`, `browser_snapshot`, `browser_evaluate`). |
| **📋 Discovered Opportunities** | Clean card or table views with location, experience, and company filters. Real-time badge indicators for MCP-extracted vs. sample data. |
| **⭐ Saved Jobs & Notes** | Bookmark jobs with automatic duplicate prevention. Add personal notes (e.g. interview dates, follow-up logs). |
| **📊 Application Tracker** | Pipeline funnel metrics (`Interested` → `Applied` → `Interview` → `Offer` → `Rejected`), CSV export, and quick status update workflow. |
| **💡 AI Role & Prep Insights** | Generates tailored skill breakdowns, responsibilities, and actionable college preparation advice using Gemini (with intelligent rule fallback). |
| **⚙️ Diagnostics & Health Checks** | Live MCP ping test, available tools explorer, demo server controls, and SQLite management. |

---

## 🛠️ Technology Stack

- **Frontend:** Streamlit
- **Language:** Python 3.10+
- **Browser Automation:** Official Playwright MCP Server (`@playwright/mcp`)
- **MCP Client:** Official Python MCP SDK (`mcp`)
- **AI Model:** Google Gemini (`google-generativeai`) with configurable model choice & heuristic fallback
- **Database:** SQLite
- **Data Processing:** Pandas

---

## 📂 Project Structure

```
ai-job-assistant/
├── app.py                      # Main Streamlit Dashboard
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── .gitignore                  # Git ignore rules
├── README.md                   # Documentation & setup guide
├── config.py                   # Configuration & environment variables
├── database.py                 # SQLite database models & queries
├── models.py                   # Data models (JobListing, Application, AISummary)
├── demo_server.py              # Lightweight local HTTP server for reliable demos
├── static/
│   └── demo_jobs.html          # Realistic fresher/student demo job portal
├── services/
│   ├── __init__.py
│   ├── mcp_client.py           # Playwright MCP client using Python MCP SDK
│   ├── job_search.py           # Job search orchestration & DOM parsing
│   └── ai_service.py           # Gemini AI analysis & preparation advice
├── pages/
│   ├── 1_Saved_Jobs.py         # Bookmarked opportunities & notes
│   ├── 2_Application_Tracker.py# Status pipeline & visual metrics
│   └── 3_Settings.py           # MCP health check, API keys & diagnostics
└── tests/
    ├── __init__.py
    ├── test_database.py        # Database operations & deduplication tests
    └── test_services.py        # AI summaries, filters, and safety tests
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites

- **Python 3.10 or higher**: Verify with `python --version`
- **Node.js 18 or higher** (with npm/npx): Verify with `node --version` and `npx --version`

### 2. Clone and Setup Environment

```bash
# Clone the repository or navigate to workspace
cd "Playwright MCP"

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
# Windows PowerShell
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

*(Optional)* Add your Gemini API key inside `.env` to enable full LLM summarization. If omitted, the application automatically uses its built-in rule analyzer so browser automation and search work completely without an API key!

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash
```

### 4. Run the Application

Launch Streamlit:

```bash
python -m streamlit run app.py
```

Open your browser at **`http://localhost:8501`**.

---

## 🎓 Step-by-Step Demonstration Workflow

Follow these steps for a live demonstration or presentation:

1. **Start the App:**
   ```bash
   python -m streamlit run app.py
   ```
2. **Perform a Real Job Search:**
   - Role / Keyword: `Data Engineer` (or `Python Developer`, `Full Stack Developer`, etc.)
   - Location: `Bengaluru` (or `Hyderabad`, `Pune`, `Remote`, etc.)
   - Experience: `Fresher` or `Internship`
   - Real Portal Target:
     - `🌐 All Real Portals (LinkedIn + Naukri + Internshala)`
     - `💼 LinkedIn Jobs (Live Public Search via Playwright MCP)`
     - `💼 Naukri.com (Live Public Search via Playwright MCP)`
     - `🎓 Internshala (Live Fresher & Internship Search via Playwright MCP)`
   - Click **"🚀 Scrape Real Job Portals with Playwright MCP"**.
3. **Observe Playwright MCP in Action:**
   - The UI displays live step-by-step progress as the Python MCP client connects to the official Playwright MCP server over `stdio`.
   - The MCP server launches headless Chromium with standard desktop User-Agent headers.
   - It executes `browser_navigate` to target portal URLs (e.g., `https://www.linkedin.com/jobs/search?...`, `https://www.naukri.com/...`, `https://internshala.com/...`).
   - It synchronizes rendering with `browser_wait_for` and inspects real DOM job cards using `browser_evaluate`.
4. **Inspect Discovered Opportunities:**
   - View the live extracted opportunities (e.g., actual openings from Amazon, Cisco, TCS, startups on Internshala, etc.).
   - Notice the **"⚡ Playwright MCP Extracted"** badge, company name, live location, experience, and real link.
5. **Generate AI Role Insights:**
   - Click **"💡 AI Job Summary"** on any job card.
   - The Gemini AI engine (or heuristic fallback) generates key technical skills, responsibilities, why the job is relevant for freshers, and preparation advice.
   - Note the student disclaimer: *General role insights based on job details (no resume uploaded).*
6. **Save to Application Tracker:**
   - Click **"⭐ Save Job"**. The job is saved into SQLite. Clicking again demonstrates duplicate prevention.
7. **Manage Status in Tracker:**
   - Click **"Application Tracker"** or **"Saved Jobs"** in the sidebar.
   - Change status from `Interested` to `Applied` or `Interview`.
   - Add notes (e.g., *"Applied on portal, scheduled interview for Friday"*).
8. **Verify Persistence:**
   - Stop and restart Streamlit (`Ctrl+C` and rerun).
   - Navigate to **"Application Tracker"**—all saved applications and updated statuses remain saved in SQLite.
9. **Settings & Health Check:**
   - Navigate to **"Settings & Diagnostics"**.
   - Click **"🧪 Ping Playwright MCP Server"** to show the live tool discovery (25 tools) and verify connectivity.

---

## 🧪 Running Automated Tests

Run the test suite verifying SQLite operations, duplicate prevention, and services:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Expected output:
```
...........
----------------------------------------------------------------------
Ran 11 tests in 0.192s

OK
```

---

## 🔧 How Playwright MCP Works in This Project

In traditional web scrapers, Python developers use custom scripts with hardcoded CSS selectors and fragile network requests.

**Model Context Protocol (MCP)** standardizes browser automation:
1. **Tool Standardization:** The browser is exposed as a standardized tool server implementing methods like `browser_navigate`, `browser_snapshot`, `browser_click`, and `browser_evaluate`.
2. **Language Boundary Crossing:** The Python MCP SDK (`mcp`) communicates with the official TypeScript Playwright MCP server over standard input/output (`stdio`), completely removing the need for manual driver installations or ad-hoc subprocess pipes.
3. **AI Agent Integration:** Any LLM that supports tool calling can query the tool list (`session.list_tools()`), read the tool schema, and issue structured tool calls directly.

---

## ❓ Troubleshooting

| Issue | Resolution |
| :--- | :--- |
| `Could not find executable 'npx'` | Ensure Node.js is installed and `npx` is available in your system's `PATH`. Run `node -v` and `npx -v` in your terminal to verify. |
| `MCP connection timed out` | The first time `npx -y @playwright/mcp@latest` runs, npm downloads the package. Run `npx -y @playwright/mcp@latest --version` in your terminal once to pre-cache the package. |
| Real portal anti-bot or access denied | Playwright MCP is configured in `config.py` with standard desktop Chrome User-Agent arguments (`--user-agent ...`), allowing live public search pages on LinkedIn, Naukri, and Internshala to load seamlessly without login. |
| Gemini API key configured | The app reads `GEMINI_API_KEY` from `.env`. When configured, it uses Google Gemini (`google-generativeai`) with REST transport. If offline or no key is present, it uses intelligent heuristic role analysis. |

---

## 📜 License

This project is licensed under the MIT License for educational and assignment purposes.
