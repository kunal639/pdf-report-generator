import asyncio
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from render import render_pdf_sync

DB_PATH = "report.db"


class CreateReportRequest(BaseModel):
    force: Optional[bool] = False


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs("reports", exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/reports")
async def create_report(
    payload: Optional[CreateReportRequest] = None,
    response: Response = None,
):
    force = payload.force if payload else False
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Idempotency check: look for an existing report generated today
    if not force:
        cursor.execute(
            """
            SELECT id, path, created_at 
            FROM reports 
            WHERE DATE(created_at) = DATE('now')
            ORDER BY id DESC 
            LIMIT 1
            """
        )
        existing_report = cursor.fetchone()
        if existing_report and os.path.exists(existing_report["path"]):
            conn.close()
            response.status_code = status.HTTP_200_OK
            return {
                "id": existing_report["id"],
                "file": f"/reports/{existing_report['id']}/file",
            }

    # Generate a fresh report
    filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join("reports", filename)

    # Offload blocking Playwright call to worker thread
    await asyncio.to_thread(render_pdf_sync, file_path)

    # Insert into reports table
    created_at = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO reports (path, created_at) VALUES (?, ?)",
        (file_path, created_at),
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    response.status_code = status.HTTP_201_CREATED
    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, path, created_at FROM reports WHERE id = ?", (report_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    return {
        "id": row["id"],
        "path": row["path"],
        "created_at": row["created_at"],
        "file": f"/reports/{row['id']}/file",
    }


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None or not os.path.exists(row["path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found",
        )

    return FileResponse(
        path=row["path"],
        media_type="application/pdf",
        filename=os.path.basename(row["path"]),
    )