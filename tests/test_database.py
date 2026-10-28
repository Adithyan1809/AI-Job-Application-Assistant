"""Unit tests for SQLite database operations and duplicate prevention."""

import os
import tempfile
import unittest
from pathlib import Path

from models import JobListing, Application, VALID_STATUSES
from database import (
    init_db,
    save_search_jobs,
    get_recent_jobs,
    save_application,
    get_applications,
    update_application_status,
    delete_application,
    get_status_counts,
    clear_search_history,
    reset_database,
    log_mcp_event,
    get_mcp_logs,
    clear_mcp_logs,
    get_mcp_log_stats
)


class TestDatabaseOperations(unittest.TestCase):
    """Test SQLite persistence, deduplication, and application tracking."""

    def setUp(self):
        # Create a unique temporary database file for each test
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_jobs.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_db(self):
        """Verify tables are created properly."""
        self.assertTrue(os.path.exists(self.db_path))

    def test_save_and_retrieve_search_jobs(self):
        """Test persisting and querying discovered jobs."""
        job1 = JobListing(
            title="Junior Data Engineer",
            company="Acme Corp",
            location="Bengaluru",
            experience="Fresher",
            salary="₹7,00,000 / year",
            description="Python & SQL",
            url="http://example.com/job/1",
            source="Test"
        )
        job2 = JobListing(
            title="Frontend Intern",
            company="Beta Inc",
            location="Remote",
            experience="Internship",
            salary="₹25,000 / month",
            description="React & CSS",
            url="http://example.com/job/2",
            source="Test"
        )
        saved = save_search_jobs([job1, job2], db_path=self.db_path)
        self.assertEqual(len(saved), 2)
        self.assertIsNotNone(saved[0].id)

        # Retrieve jobs
        all_jobs = get_recent_jobs(db_path=self.db_path)
        self.assertEqual(len(all_jobs), 2)

        # Filter by role
        de_jobs = get_recent_jobs(role="Data Engineer", db_path=self.db_path)
        self.assertEqual(len(de_jobs), 1)
        self.assertEqual(de_jobs[0].title, "Junior Data Engineer")

    def test_save_application_and_duplicate_prevention(self):
        """Test saving a job to tracker and verifying duplicate bookmark prevention."""
        job = JobListing(
            title="Python Developer",
            company="Tech Soft",
            location="Bengaluru",
            experience="0-1 years",
            salary="₹6,00,000 / year",
            description="FastAPI & SQLite",
            url="http://example.com/job/3",
            source="Playwright MCP"
        )
        
        # 1st save: should succeed
        ok1, msg1, app_id1 = save_application(job, status="Interested", db_path=self.db_path)
        self.assertTrue(ok1)
        self.assertIsNotNone(app_id1)

        # 2nd save with exact same title, company, url: must be rejected
        ok2, msg2, app_id2 = save_application(job, status="Applied", db_path=self.db_path)
        self.assertFalse(ok2)
        self.assertIn("already bookmarked", msg2.lower())
        self.assertEqual(app_id1, app_id2)

        # Confirm only 1 application in database
        apps = get_applications(db_path=self.db_path)
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].title, "Python Developer")

    def test_update_application_status_and_notes(self):
        """Test changing status across the pipeline and adding notes."""
        job = JobListing(
            title="Cloud Engineer",
            company="CloudWorks",
            location="Hyderabad",
            experience="1-2 years",
            salary="₹8,00,000 / year",
            description="AWS & Terraform",
            url="http://example.com/job/4"
        )
        _, _, app_id = save_application(job, status="Interested", db_path=self.db_path)

        # Update to Applied
        success = update_application_status(app_id, "Applied", notes="Submitted resume on 26 Oct", db_path=self.db_path)
        self.assertTrue(success)

        apps = get_applications(status="Applied", db_path=self.db_path)
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].status, "Applied")
        self.assertIn("Submitted resume", apps[0].notes)

        # Update to Interview
        update_application_status(app_id, "Interview", db_path=self.db_path)
        apps_interview = get_applications(status="Interview", db_path=self.db_path)
        self.assertEqual(len(apps_interview), 1)

    def test_get_status_counts(self):
        """Test status counts for dashboard metrics."""
        for i, status in enumerate(["Interested", "Applied", "Applied", "Interview", "Offer"]):
            job = JobListing(
                title=f"Role {i}",
                company=f"Company {i}",
                location="Bengaluru",
                experience="Fresher",
                salary="₹5,00,000",
                description="Test",
                url=f"http://example.com/job/{i}"
            )
            save_application(job, status=status, db_path=self.db_path)

        counts = get_status_counts(db_path=self.db_path)
        self.assertEqual(counts["Interested"], 1)
        self.assertEqual(counts["Applied"], 2)
        self.assertEqual(counts["Interview"], 1)
        self.assertEqual(counts["Offer"], 1)
        self.assertEqual(counts["Rejected"], 0)

    def test_delete_application(self):
        """Test removing an application from the tracker."""
        job = JobListing(
            title="QA Engineer",
            company="QualityFirst",
            location="Pune",
            experience="0-1 years",
            salary="₹5,00,000",
            description="Testing",
            url="http://example.com/job/qa"
        )
        _, _, app_id = save_application(job, db_path=self.db_path)
        self.assertEqual(len(get_applications(db_path=self.db_path)), 1)

        deleted = delete_application(app_id, db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertEqual(len(get_applications(db_path=self.db_path)), 0)

    def test_mcp_logging_and_filtering(self):
        """Test persisting and querying detailed MCP execution logs."""
        id1 = log_mcp_event(
            event_type="SESSION_START",
            tool_name="client.connect",
            arguments={"command": "npx", "args": ["@playwright/mcp@latest"]},
            status="INFO",
            db_path=self.db_path
        )
        self.assertGreater(id1, 0)

        id2 = log_mcp_event(
            event_type="TOOL_RESULT",
            tool_name="browser_navigate",
            arguments={"url": "https://www.linkedin.com/jobs"},
            response="Navigated to 200 OK",
            duration_ms=145.2,
            status="SUCCESS",
            db_path=self.db_path
        )
        self.assertGreater(id2, 0)

        id3 = log_mcp_event(
            event_type="TOOL_ERROR",
            tool_name="browser_evaluate",
            arguments={"function": "() => error"},
            error_message="ReferenceError: error is not defined",
            duration_ms=35.0,
            status="ERROR",
            db_path=self.db_path
        )
        self.assertGreater(id3, 0)

        # Check total logs retrieved
        all_logs = get_mcp_logs(db_path=self.db_path)
        self.assertEqual(len(all_logs), 3)

        # Filter by status
        err_logs = get_mcp_logs(status="ERROR", db_path=self.db_path)
        self.assertEqual(len(err_logs), 1)
        self.assertEqual(err_logs[0]["tool_name"], "browser_evaluate")

        # Filter by tool
        nav_logs = get_mcp_logs(tool_name="browser_navigate", db_path=self.db_path)
        self.assertEqual(len(nav_logs), 1)
        self.assertEqual(nav_logs[0]["status"], "SUCCESS")

        # Filter by search keyword
        search_logs = get_mcp_logs(search="linkedin", db_path=self.db_path)
        self.assertEqual(len(search_logs), 1)

        # Stats calculation
        stats = get_mcp_log_stats(db_path=self.db_path)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["success_cnt"], 1)
        self.assertEqual(stats["error_cnt"], 1)
        self.assertGreater(stats["avg_duration_ms"], 0)

        # Clear logs
        clear_mcp_logs(db_path=self.db_path)
        self.assertEqual(len(get_mcp_logs(db_path=self.db_path)), 0)


if __name__ == "__main__":
    unittest.main()
