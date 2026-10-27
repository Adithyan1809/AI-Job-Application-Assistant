"""AI Service using Gemini API (with heuristic fallbacks) for job extraction and analysis."""

import os
import re
import json
from typing import Optional, List, Dict, Any
from config import GEMINI_API_KEY, LLM_MODEL, is_gemini_configured
from models import JobListing, AISummary

# Attempt to configure google.generativeai if API key is present
_gemini_client = None


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Helper to extract JSON object or array from markdown fenced code blocks or raw text."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        return json.loads(text)
    except Exception:
        start_dict = text.find("{")
        end_dict = text.rfind("}")
        if start_dict != -1 and end_dict != -1 and end_dict > start_dict:
            try:
                return json.loads(text[start_dict : end_dict + 1])
            except Exception:
                pass
        start_arr = text.find("[")
        end_arr = text.rfind("]")
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            try:
                return json.loads(text[start_arr : end_arr + 1])
            except Exception:
                pass
    return None


def _call_gemini_api(prompt: str) -> Optional[Dict[str, Any]]:
    """Query Gemini with automatic model name fallback and REST transport."""
    if not is_gemini_configured():
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY, transport="rest")
        
        candidates = [LLM_MODEL, "models/gemini-flash-latest", "gemini-1.5-flash", "models/gemini-2.5-flash", "models/gemini-3.8-flash"]
        seen = set()
        unique_models = [m for m in candidates if m and not (m in seen or seen.add(m))]

        for mod_name in unique_models:
            try:
                model = genai.GenerativeModel(mod_name)
                response = model.generate_content(prompt)
                if response and hasattr(response, "text") and response.text:
                    parsed = extract_json_from_text(response.text)
                    if parsed and isinstance(parsed, dict):
                        return parsed
            except Exception:
                continue
    except Exception as e:
        print(f"Gemini service error: {e}")
    return None


def generate_job_summary(job: JobListing) -> AISummary:
    """
    Generate a concise AI summary and interview preparation guide for a job.
    Uses Gemini when configured, or heuristic intelligent breakdown otherwise.
    Never claims to match a personal resume unless a resume is provided.
    """
    prompt = f"""
You are an expert technical career advisor for university students and early-career job seekers.
Analyze this job posting and output ONLY a valid JSON object:

{{
  "required_skills": ["skill1", "skill2", "skill3"],
  "responsibilities": ["duty1", "duty2"],
  "experience_requirements": "Summary of experience required",
  "prep_advice": ["Actionable step 1 for students/freshers", "Actionable step 2"],
  "relevance_explanation": "2-3 sentences explaining why this job is great for early career applicants"
}}

Job Details:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Experience: {job.experience}
- Salary: {job.salary}
- Description:
{job.description}

Important: Return ONLY valid JSON, no conversational markdown.
"""
    data = _call_gemini_api(prompt)
    if data and isinstance(data, dict):
        return AISummary(
            job_title=job.title,
            company=job.company,
            required_skills=data.get("required_skills", []),
            responsibilities=data.get("responsibilities", []),
            experience_requirements=data.get("experience_requirements", job.experience or "Entry-level"),
            prep_advice=data.get("prep_advice", []),
            relevance_explanation=data.get("relevance_explanation", ""),
            is_ai_generated=True,
        )

    # Heuristic fallback summary
    return _generate_heuristic_summary(job)


def _generate_heuristic_summary(job: JobListing) -> AISummary:
    """Intelligent template-based analyzer for offline / non-API environments."""
    desc = job.description.lower()
    
    # Common tech keywords to scan
    tech_keywords = [
        "python", "sql", "java", "c++", "javascript", "react", "fastapi", "django",
        "spark", "kafka", "aws", "gcp", "azure", "docker", "kubernetes", "git",
        "linux", "pandas", "pytorch", "scikit-learn", "data structures", "algorithms",
        "oop", "playwright", "selenium", "bigquery", "rest api", "nosql", "postgresql"
    ]
    detected_skills = [kw.title() for kw in tech_keywords if re.search(r"\b" + re.escape(kw) + r"\b", desc)]
    if not detected_skills:
        detected_skills = ["Problem Solving", "Python / Programming Fundamentals", "Database Basics", "Communication"]
    
    # Extract responsibilities from sentences or bullet points
    responsibilities = []
    lines = [line.strip() for line in job.description.split("\n") if line.strip()]
    for line in lines:
        if line.startswith(("-", "•", "*", "1.", "2.", "3.")) or "build" in line.lower() or "develop" in line.lower() or "design" in line.lower():
            clean = re.sub(r"^[-•*\d.]+\s*", "", line).strip()
            if len(clean) > 20:
                responsibilities.append(clean)
                if len(responsibilities) >= 4:
                    break
    if not responsibilities:
        responsibilities = [
            f"Assist in development, testing, and deployment of software solutions for {job.company}.",
            "Collaborate with senior software engineers on code reviews and feature implementation.",
            "Write clean, well-tested code and maintain project documentation."
        ]
        
    # Fresher preparation advice
    prep_advice = [
        f"Master the core technical stack: Revise {', '.join(detected_skills[:3])} fundamentals thoroughly.",
        "Build a showcase portfolio project: Create a small end-to-end repository on GitHub demonstrating these skills.",
        "Prepare Data Structures & Algorithms: Practice basic array, hash map, and SQL query problems on LeetCode.",
        "Tailor your application narrative: Highlight college coursework, internships, and relevant personal projects in your cover letter."
    ]
    
    relevance_explanation = (
        f"This position at {job.company} provides an excellent starting point for freshers and early-career developers. "
        f"The role exposes you to {', '.join(detected_skills[:2])} in a real-world environment while offering mentorship."
    )
    
    return AISummary(
        job_title=job.title,
        company=job.company,
        required_skills=detected_skills,
        responsibilities=responsibilities,
        experience_requirements=job.experience or "Fresher / 0-1 Years",
        prep_advice=prep_advice,
        relevance_explanation=relevance_explanation,
        is_ai_generated=False,
    )
