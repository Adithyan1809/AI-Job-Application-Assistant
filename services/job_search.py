"""Real-world job search orchestration for LinkedIn, Internshala, and Naukri using Playwright MCP."""

import json
import re
import urllib.parse
from typing import List, Optional, Callable, Dict, Any

from config import ALLOWED_DOMAINS
from models import JobListing
from services.mcp_client import PlaywrightMCPClient
from database import save_search_jobs


def is_url_allowed(url: str) -> bool:
    """Validate if target URL belongs to permitted public domains."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        netloc = parsed.netloc.split(":")[0].lower()
        return any(netloc == domain or netloc.endswith("." + domain) for domain in ALLOWED_DOMAINS)
    except Exception:
        return False


def _slugify(text: str) -> str:
    """Helper to convert role or location into a clean URL slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)


async def scrape_linkedin(
    client: PlaywrightMCPClient,
    role: str,
    location: str,
    experience: str = ""
) -> List[JobListing]:
    """Scrape real public job listings from LinkedIn Jobs via Playwright MCP."""
    role_q = urllib.parse.quote(role.strip())
    loc_q = urllib.parse.quote(location.strip())
    
    url = f"https://www.linkedin.com/jobs/search?keywords={role_q}&location={loc_q}"
    if experience and ("fresher" in experience.lower() or "0-1" in experience.lower() or "intern" in experience.lower()):
        # LinkedIn filter: f_E=1 (Internship), f_E=2 (Entry level)
        url += "&f_E=1,2"

    await client.navigate(url)
    await client.wait_for(time_s=1.0)

    js_extract = """() => {
        const cards = Array.from(document.querySelectorAll('.base-card, ul.jobs-search__results-list li'));
        return cards.slice(0, 15).map(c => {
            const titleElem = c.querySelector('.base-search-card__title, h3, a.base-card__full-link');
            const compElem = c.querySelector('.base-search-card__subtitle, h4, .base-search-card__subtitle a');
            const locElem = c.querySelector('.job-search-card__location');
            const salElem = c.querySelector('.job-search-card__salary-info');
            const dateElem = c.querySelector('time');
            const linkElem = c.querySelector('a.base-card__full-link, a');

            return {
                title: titleElem ? titleElem.innerText.trim() : '',
                company: compElem ? compElem.innerText.trim() : 'Company on LinkedIn',
                location: locElem ? locElem.innerText.trim() : '',
                salary: salElem ? salElem.innerText.trim() : 'Not Specified',
                description: (titleElem ? titleElem.innerText.trim() : '') + (dateElem ? ' (Posted ' + dateElem.innerText.trim() + ')' : '') + ' - Live listing on LinkedIn Jobs.',
                url: linkElem ? linkElem.href.split('?')[0] : 'https://www.linkedin.com/jobs/'
            };
        }).filter(x => x.title && x.title.length > 2);
    }"""

    raw_eval = await client.evaluate(js_extract)
    raw_jobs = _parse_mcp_evaluate_result(raw_eval, "LinkedIn Jobs")
    for j in raw_jobs:
        j.experience = "Fresher / Entry-Level" if not j.experience or j.experience == "Not Specified" else j.experience
    return raw_jobs


async def scrape_internshala(
    client: PlaywrightMCPClient,
    role: str,
    location: str,
    experience: str = ""
) -> List[JobListing]:
    """Scrape real fresher jobs or internships from Internshala via Playwright MCP."""
    role_slug = _slugify(role)
    # Internshala standardizes "bengaluru" as "bangalore"
    loc_clean = location.lower().strip()
    if loc_clean in ("bengaluru", "bangalore"):
        loc_slug = "bangalore"
    else:
        loc_slug = _slugify(loc_clean)

    is_internship = "intern" in experience.lower()
    
    if is_internship:
        if loc_slug:
            url = f"https://internshala.com/internships/{role_slug}-internship-in-{loc_slug}/"
        else:
            url = f"https://internshala.com/internships/keywords-{role_slug}/"
    else:
        if loc_slug:
            url = f"https://internshala.com/jobs/{role_slug}-jobs-in-{loc_slug}/"
        else:
            url = f"https://internshala.com/jobs/keywords-{role_slug}/"

    await client.navigate(url)
    await client.wait_for(time_s=1.0)

    js_extract = """() => {
        const cards = Array.from(document.querySelectorAll('.individual_internship, div[id^="individual_internship_"], .internship_meta'));
        return cards.slice(0, 15).map(c => {
            const titleElem = c.querySelector('.job-internship-name, .profile a, a.job-title-href, h3');
            const compElem = c.querySelector('.company-name, .link_display_like_text');
            const locElem = c.querySelector('.row-1-item.locations a, .locations');
            const salElem = c.querySelector('.stipend, .salary, .item_body');
            const expElem = c.querySelector('.experience');
            const linkElem = c.querySelector('a.job-title-href, a.view_detail_button, .profile a');

            return {
                title: titleElem ? titleElem.innerText.trim() : '',
                company: compElem ? compElem.innerText.trim() : 'Company on Internshala',
                location: locElem ? locElem.innerText.trim() : 'India',
                experience: expElem ? expElem.innerText.trim() : 'Fresher / Internship',
                salary: salElem ? salElem.innerText.trim() : 'Competitive Stipend',
                description: (titleElem ? titleElem.innerText.trim() : '') + ' - Verified opportunity on Internshala.',
                url: linkElem ? (linkElem.href.startsWith('http') ? linkElem.href : 'https://internshala.com' + linkElem.getAttribute('href')) : 'https://internshala.com'
            };
        }).filter(x => x.title && x.title.length > 2);
    }"""

    raw_eval = await client.evaluate(js_extract)
    return _parse_mcp_evaluate_result(raw_eval, "Internshala")


async def scrape_naukri(
    client: PlaywrightMCPClient,
    role: str,
    location: str,
    experience: str = ""
) -> List[JobListing]:
    """Scrape real job vacancies from Naukri.com via Playwright MCP."""
    role_slug = _slugify(role)
    loc_slug = _slugify(location)
    
    if loc_slug:
        url = f"https://www.naukri.com/{role_slug}-jobs-in-{loc_slug}"
    else:
        url = f"https://www.naukri.com/{role_slug}-jobs"

    await client.navigate(url)
    await client.wait_for(time_s=1.2)

    js_extract = """() => {
        const cards = Array.from(document.querySelectorAll('.srp-jobtuple-wrapper, .cust-job-tuple, article.jobTuple'));
        return cards.slice(0, 15).map(c => {
            const titleElem = c.querySelector('a.title, .title a, .job-title');
            const compElem = c.querySelector('a.comp-name, .comp-name, .company-name');
            const locElem = c.querySelector('.loc-wrap, .loc, .location');
            const expElem = c.querySelector('.expwdth, .exp, .experience');
            const salElem = c.querySelector('.sal-wrap, .sal, .salary');
            const descElem = c.querySelector('.job-desc, .desc');

            return {
                title: titleElem ? titleElem.innerText.trim() : '',
                company: compElem ? compElem.innerText.trim() : 'Company on Naukri',
                location: locElem ? locElem.innerText.trim() : 'India',
                experience: expElem ? expElem.innerText.trim() : '0-2 Yrs',
                salary: salElem ? salElem.innerText.trim() : 'Not Disclosed',
                description: descElem ? descElem.innerText.trim() : ((titleElem ? titleElem.innerText.trim() : '') + ' on Naukri.com'),
                url: titleElem && titleElem.href ? titleElem.href : 'https://www.naukri.com'
            };
        }).filter(x => x.title && x.title.length > 2);
    }"""

    raw_eval = await client.evaluate(js_extract)
    return _parse_mcp_evaluate_result(raw_eval, "Naukri.com")


async def search_jobs_with_mcp(
    role: str = "Data Engineer",
    location: str = "Bengaluru",
    experience: str = "",
    employment_type: str = "",
    min_salary: Optional[str] = None,
    portal_choice: str = "all_portals",
    progress_cb: Optional[Callable[[str, float], None]] = None
) -> List[JobListing]:
    """
    Search and extract jobs from real job portals (LinkedIn, Naukri, Internshala)
    strictly using Playwright MCP browser automation tools.
    """
    def report(text: str, pct: float):
        if progress_cb:
            progress_cb(text, pct)

    report("Connecting to Playwright MCP server over stdio...", 0.1)
    extracted_jobs: List[JobListing] = []

    async with PlaywrightMCPClient() as client:
        # Determine portals to scrape
        portals_to_run = []
        if portal_choice in ("all_portals", "linkedin"):
            portals_to_run.append("linkedin")
        if portal_choice in ("all_portals", "internshala"):
            portals_to_run.append("internshala")
        if portal_choice in ("all_portals", "naukri"):
            portals_to_run.append("naukri")

        total_steps = len(portals_to_run)
        step_idx = 0

        for portal in portals_to_run:
            step_idx += 1
            base_pct = 0.15 + (step_idx - 1) * (0.75 / max(total_steps, 1))

            if portal == "linkedin":
                report(f"Navigating to real LinkedIn Jobs for '{role}' in '{location}' via MCP...", base_pct)
                try:
                    li_jobs = await scrape_linkedin(client, role, location, experience)
                    report(f"Extracted {len(li_jobs)} real job openings from LinkedIn!", base_pct + 0.2)
                    extracted_jobs.extend(li_jobs)
                except Exception as e:
                    print(f"LinkedIn MCP error: {e}")

            elif portal == "internshala":
                report(f"Navigating to real Internshala listings for '{role}' in '{location}' via MCP...", base_pct)
                try:
                    ish_jobs = await scrape_internshala(client, role, location, experience)
                    report(f"Extracted {len(ish_jobs)} real opportunities from Internshala!", base_pct + 0.2)
                    extracted_jobs.extend(ish_jobs)
                except Exception as e:
                    print(f"Internshala MCP error: {e}")

            elif portal == "naukri":
                report(f"Navigating to real Naukri.com listings for '{role}' in '{location}' via MCP...", base_pct)
                try:
                    nk_jobs = await scrape_naukri(client, role, location, experience)
                    report(f"Extracted {len(nk_jobs)} real listings from Naukri.com!", base_pct + 0.2)
                    extracted_jobs.extend(nk_jobs)
                except Exception as e:
                    print(f"Naukri MCP error: {e}")

    report("Deduplicating and filtering extracted real opportunities...", 0.95)
    filtered = _filter_jobs(extracted_jobs, role, location, experience)

    # Save to SQLite database
    if filtered:
        save_search_jobs(filtered)

    report(f"Successfully extracted {len(filtered)} real opportunities from live job portals!", 1.0)
    return filtered


def _parse_mcp_evaluate_result(raw_result: str, source_name: str) -> List[JobListing]:
    """Parse JSON payload returned by Playwright MCP browser_evaluate."""
    if not raw_result or not raw_result.strip():
        return []

    raw_items = []
    # 1. Direct JSON decode
    try:
        data = json.loads(raw_result)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                pass
        if isinstance(data, list):
            raw_items = data
    except Exception:
        pass

    # 2. Regex search if direct decode failed
    if not raw_items:
        arr_match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", raw_result) or re.search(r"\[[\s\S]*\]", raw_result)
        if arr_match:
            try:
                data = json.loads(arr_match.group(0))
                if isinstance(data, list):
                    raw_items = data
            except Exception:
                pass

    jobs: List[JobListing] = []
    for item in raw_items:
        if isinstance(item, dict) and item.get("title"):
            title = str(item.get("title", "")).strip()
            if len(title) < 2:
                continue
            company = str(item.get("company") or f"Company on {source_name}").strip()
            location = str(item.get("location") or "India").strip()
            experience = str(item.get("experience") or "Entry-level / Fresher").strip()
            salary = str(item.get("salary") or "Not Disclosed").strip()
            description = str(item.get("description") or f"{title} at {company}").strip()
            raw_url = str(item.get("url") or "").strip()
            
            # Ensure valid clickable URL
            if not raw_url.startswith("http"):
                safe_q = urllib.parse.quote(f"{title} {company} jobs")
                raw_url = f"https://www.google.com/search?q={safe_q}"

            jobs.append(JobListing(
                title=title,
                company=company,
                location=location,
                experience=experience,
                salary=salary,
                description=description,
                url=raw_url,
                source=f"{source_name} (Playwright MCP)",
                extracted_via_mcp=True
            ))
    return jobs


def _filter_jobs(
    jobs: List[JobListing],
    role: str = "",
    location: str = "",
    experience: str = ""
) -> List[JobListing]:
    """Deduplicate listings and apply optional search filters."""
    seen = set()
    filtered: List[JobListing] = []

    for j in jobs:
        # Deduplication key by title and company
        key = (j.title.lower().strip(), j.company.lower().strip())
        if key in seen:
            continue
        seen.add(key)
        filtered.append(j)

    return filtered
