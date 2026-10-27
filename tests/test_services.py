"""Unit tests for real portal services, data filtering, AI summarization, and security guardrails."""

import unittest
from models import JobListing, AISummary
from services.job_search import is_url_allowed, _filter_jobs, _slugify
from services.ai_service import generate_job_summary, _generate_heuristic_summary
from services.mcp_client import PlaywrightMCPClient


class TestServices(unittest.TestCase):
    """Test AI services, URL safety validation, and job filtering."""

    def test_url_security_whitelist(self):
        """Verify URL validation permits whitelisted real portals and rejects arbitrary URLs."""
        # Permitted real portals
        self.assertTrue(is_url_allowed("https://www.linkedin.com/jobs/search"))
        self.assertTrue(is_url_allowed("https://www.naukri.com/data-engineer-jobs"))
        self.assertTrue(is_url_allowed("https://internshala.com/jobs/"))
        self.assertTrue(is_url_allowed("https://www.python.org/jobs/"))

        # Forbidden
        self.assertFalse(is_url_allowed("https://malicious-website.com/"))
        self.assertFalse(is_url_allowed("ftp://linkedin.com/"))
        self.assertFalse(is_url_allowed("javascript:alert(1)"))
        self.assertFalse(is_url_allowed("file:///etc/passwd"))

    def test_slugify(self):
        """Verify role and location slug creation for real portals."""
        self.assertEqual(_slugify("Data Engineer"), "data-engineer")
        self.assertEqual(_slugify("Bengaluru / Bangalore"), "bengaluru-bangalore")
        self.assertEqual(_slugify("Python & FastAPI Developer"), "python-fastapi-developer")

    def test_filter_jobs(self):
        """Test filtering and deduplicating real job listings."""
        jobs = [
            JobListing(
                title="Junior Data Engineer",
                company="Amazon",
                location="Bengaluru",
                experience="Fresher / 0-1 years",
                description="Python and SQL ETL pipelines",
                url="https://in.linkedin.com/jobs/view/1",
                source="LinkedIn Jobs (Playwright MCP)"
            ),
            JobListing(
                title="Frontend Developer",
                company="StoryYell",
                location="Remote",
                experience="Internship",
                description="React and JavaScript",
                url="https://internshala.com/job/detail/2",
                source="Internshala (Playwright MCP)"
            ),
            # Duplicate of first
            JobListing(
                title="Junior Data Engineer",
                company="Amazon",
                location="Bengaluru",
                experience="Fresher / 0-1 years",
                description="Python and SQL ETL pipelines",
                url="https://in.linkedin.com/jobs/view/1-dup",
                source="LinkedIn Jobs (Playwright MCP)"
            )
        ]

        # 1. Deduplication check
        filtered_all = _filter_jobs(jobs)
        self.assertEqual(len(filtered_all), 2)
        self.assertEqual(filtered_all[0].company, "Amazon")
        self.assertEqual(filtered_all[1].company, "StoryYell")

    def test_heuristic_ai_summary(self):
        """Ensure heuristic fallback extracts skills, responsibilities, prep advice, and disclaimer."""
        job = JobListing(
            title="Data Engineer I",
            company="Amazon",
            location="Bengaluru",
            experience="Fresher",
            salary="₹12,00,000",
            description="Looking for engineers with Python, SQL, and Apache Spark to build big data pipelines and AWS analytics.",
            url="https://in.linkedin.com/jobs/view/1"
        )
        summary = _generate_heuristic_summary(job)
        self.assertIsInstance(summary, AISummary)
        self.assertEqual(summary.job_title, job.title)
        self.assertEqual(summary.company, job.company)
        
        # Verify extracted tech skills
        skills_lower = [s.lower() for s in summary.required_skills]
        self.assertIn("python", skills_lower)
        self.assertIn("sql", skills_lower)
        self.assertIn("spark", skills_lower)
        self.assertIn("aws", skills_lower)
        
        # Verify preparation advice exists
        self.assertGreaterEqual(len(summary.prep_advice), 2)
        
        # Verify disclaimer does not claim personal resume match
        self.assertIn("No resume was analyzed", summary.disclaimer)

    def test_mcp_client_executable_resolution(self):
        """Verify PlaywrightMCPClient properly resolves executable on OS."""
        client = PlaywrightMCPClient()
        resolved = client._resolve_executable()
        self.assertIsNotNone(resolved)
        self.assertTrue(len(resolved) > 0)

    def test_portal_info_detection(self):
        """Verify portal identification correctly tags LinkedIn, Naukri, Internshala, and Glassdoor."""
        from models import get_portal_info
        
        p_li = get_portal_info("https://www.linkedin.com/jobs/view/123", "")
        self.assertEqual(p_li["name"], "LinkedIn")
        self.assertIn("linkedin", p_li["domain"])

        p_nk = get_portal_info("https://www.naukri.com/job-listings-123", "")
        self.assertEqual(p_nk["name"], "Naukri")
        self.assertIn("naukri", p_nk["domain"])

        p_ish = get_portal_info("https://internshala.com/job/detail/123", "")
        self.assertEqual(p_ish["name"], "Internshala")
        self.assertIn("internshala", p_ish["domain"])

        p_gd = get_portal_info("https://www.glassdoor.com/job-listing/123", "")
        self.assertEqual(p_gd["name"], "Glassdoor")
        self.assertIn("glassdoor", p_gd["domain"])

    def test_parse_mcp_evaluate_result_edge_cases(self):
        """Verify _parse_mcp_evaluate_result handles empty strings, malformed text, and invalid URLs."""
        from services.job_search import _parse_mcp_evaluate_result

        # Empty string
        self.assertEqual(_parse_mcp_evaluate_result("", "LinkedIn"), [])
        self.assertEqual(_parse_mcp_evaluate_result("[]", "Naukri"), [])
        self.assertEqual(_parse_mcp_evaluate_result("not valid json", "Test"), [])

        # Valid array with missing/relative URL
        raw = '[{"title": "Software Intern", "company": "TechCorp", "url": "/job/123"}]'
        parsed = _parse_mcp_evaluate_result(raw, "Internshala")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].title, "Software Intern")
        # URL should be sanitized to http
        self.assertTrue(parsed[0].url.startswith("http"))

    def test_extract_json_from_text(self):
        """Verify JSON extractor correctly parses markdown code blocks and raw dictionaries."""
        from services.ai_service import extract_json_from_text

        # Fenced markdown
        fenced = "```json\n{\"skills\": [\"Python\", \"SQL\"]}\n```"
        self.assertEqual(extract_json_from_text(fenced), {"skills": ["Python", "SQL"]})

        # Text with preamble
        preamble = "Here is the summary:\n{\"role\": \"Engineer\"}\nHope this helps!"
        self.assertEqual(extract_json_from_text(preamble), {"role": "Engineer"})

        # Invalid
        self.assertIsNone(extract_json_from_text("no json here"))


if __name__ == "__main__":
    unittest.main()
