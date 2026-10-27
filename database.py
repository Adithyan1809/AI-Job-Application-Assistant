"""SQLite database layer for persisting jobs and application tracking."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Generator
from config import DATABASE_PATH
from models import JobListing, Application, VALID_STATUSES


def get_connection(db_path: str = DATABASE_PATH) -> sqlite3.Connection:
    """Create a connection with sqlite3 Row factory and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db(db_path: str = DATABASE_PATH) -> Generator[sqlite3.Cursor, None, None]:
    """Context manager that commits and always closes the SQLite connection."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = DATABASE_PATH) -> None:
    """Initialize database tables and indexes."""
    with get_db(db_path) as cursor:
        # Table for search results / discovered jobs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                experience TEXT,
                salary TEXT,
                description TEXT,
                url TEXT,
                source TEXT,
                extracted_via_mcp INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table for tracked applications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                experience TEXT,
                salary TEXT,
                description TEXT,
                url TEXT,
                status TEXT NOT NULL DEFAULT 'Interested',
                notes TEXT DEFAULT '',
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, company, url),
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status)")


def save_search_jobs(jobs: List[JobListing], db_path: str = DATABASE_PATH) -> List[JobListing]:
    """Save newly discovered jobs into the search history, returning updated jobs with IDs."""
    if not jobs:
        return []
        
    saved_jobs = []
    with get_db(db_path) as cursor:
        for job in jobs:
            cursor.execute("""
                INSERT INTO jobs (title, company, location, experience, salary, description, url, source, extracted_via_mcp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.title,
                job.company,
                job.location,
                job.experience,
                job.salary,
                job.description,
                job.url,
                job.source,
                1 if job.extracted_via_mcp else 0,
                job.created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            job.id = cursor.lastrowid
            saved_jobs.append(job)
    return saved_jobs


def get_recent_jobs(
    limit: int = 100,
    role: Optional[str] = None,
    location: Optional[str] = None,
    db_path: str = DATABASE_PATH
) -> List[JobListing]:
    """Retrieve recent jobs from search history with optional filters."""
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if role and role.strip():
        query += " AND (title LIKE ? OR description LIKE ?)"
        term = f"%{role.strip()}%"
        params.extend([term, term])
        
    if location and location.strip():
        query += " AND location LIKE ?"
        params.append(f"%{location.strip()}%")
        
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    jobs = []
    with get_db(db_path) as cursor:
        cursor.execute(query, params)
        for row in cursor.fetchall():
            jobs.append(JobListing(
                id=row["id"],
                title=row["title"],
                company=row["company"],
                location=row["location"],
                experience=row["experience"],
                salary=row["salary"],
                description=row["description"],
                url=row["url"],
                source=row["source"],
                extracted_via_mcp=bool(row["extracted_via_mcp"]),
                created_at=row["created_at"],
            ))
    return jobs


def save_application(
    job: JobListing,
    status: str = "Interested",
    notes: str = "",
    db_path: str = DATABASE_PATH
) -> Tuple[bool, str, Optional[int]]:
    """
    Save a job as an application bookmark.
    Prevents duplicate entries (by title, company, url).
    Returns (success: bool, message: str, application_id: Optional[int]).
    """
    if status not in VALID_STATUSES:
        status = "Interested"
        
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db(db_path) as cursor:
        cursor.execute("""
            SELECT id, status FROM applications 
            WHERE title = ? AND company = ? AND url = ?
        """, (job.title, job.company, job.url))
        existing = cursor.fetchone()
        
        if existing:
            return False, f"Job already bookmarked with status '{existing['status']}'", existing["id"]
            
        cursor.execute("""
            INSERT INTO applications (job_id, title, company, location, experience, salary, description, url, status, notes, saved_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.id,
            job.title,
            job.company,
            job.location,
            job.experience,
            job.salary,
            job.description,
            job.url,
            status,
            notes,
            now,
            now
        ))
        return True, "Job successfully saved to Application Tracker!", cursor.lastrowid


def get_applications(status: Optional[str] = None, db_path: str = DATABASE_PATH) -> List[Application]:
    """Retrieve all tracked applications, optionally filtered by status."""
    query = "SELECT * FROM applications WHERE 1=1"
    params = []
    
    if status and status in VALID_STATUSES:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY updated_at DESC"
    
    apps = []
    with get_db(db_path) as cursor:
        cursor.execute(query, params)
        for row in cursor.fetchall():
            apps.append(Application(
                id=row["id"],
                job_id=row["job_id"],
                title=row["title"],
                company=row["company"],
                location=row["location"],
                experience=row["experience"],
                salary=row["salary"],
                description=row["description"],
                url=row["url"],
                status=row["status"],
                notes=row["notes"] or "",
                saved_at=row["saved_at"],
                updated_at=row["updated_at"],
            ))
    return apps


def update_application_status(
    app_id: int,
    new_status: str,
    notes: Optional[str] = None,
    db_path: str = DATABASE_PATH
) -> bool:
    """Update status and optional notes for an application."""
    if new_status not in VALID_STATUSES:
        return False
        
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db(db_path) as cursor:
        if notes is not None:
            cursor.execute("""
                UPDATE applications
                SET status = ?, notes = ?, updated_at = ?
                WHERE id = ?
            """, (new_status, notes, now, app_id))
        else:
            cursor.execute("""
                UPDATE applications
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (new_status, now, app_id))
        return cursor.rowcount > 0


def delete_application(app_id: int, db_path: str = DATABASE_PATH) -> bool:
    """Delete an application from the tracker."""
    with get_db(db_path) as cursor:
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        return cursor.rowcount > 0


def get_status_counts(db_path: str = DATABASE_PATH) -> Dict[str, int]:
    """Get count of applications for each status."""
    counts = {s: 0 for s in VALID_STATUSES}
    with get_db(db_path) as cursor:
        cursor.execute("SELECT status, COUNT(*) as cnt FROM applications GROUP BY status")
        for row in cursor.fetchall():
            if row["status"] in counts:
                counts[row["status"]] = row["cnt"]
    return counts


def clear_search_history(db_path: str = DATABASE_PATH) -> None:
    """Clear cached search jobs."""
    with get_db(db_path) as cursor:
        cursor.execute("DELETE FROM jobs")


def reset_database(db_path: str = DATABASE_PATH) -> None:
    """Drop and recreate all tables."""
    with get_db(db_path) as cursor:
        cursor.execute("DROP TABLE IF EXISTS applications")
        cursor.execute("DROP TABLE IF EXISTS jobs")
    init_db(db_path)
