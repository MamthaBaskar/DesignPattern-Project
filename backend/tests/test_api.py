"""
Integration tests for FastAPI endpoints.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "pdf" in data["supported_formats"]


def test_api_compare_txt():
    v1_path = SAMPLES_DIR / "attendance_v1.txt"
    v2_path = SAMPLES_DIR / "attendance_v2.txt"

    with open(v1_path, "rb") as f1, open(v2_path, "rb") as f2:
        res = client.post(
            "/api/compare",
            files={
                "old_file": ("attendance_v1.txt", f1, "text/plain"),
                "new_file": ("attendance_v2.txt", f2, "text/plain"),
            },
            data={"strategy": "semantic"},
        )

    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "changes" in data
    assert data["summary"]["total_changes"] >= 1

    # Verify that the 75% -> 80% change is captured with High importance
    req_changes = [c for c in data["changes"] if "75%" in c.get("old_text", "") and "80%" in c.get("new_text", "")]
    assert len(req_changes) == 1
    assert req_changes[0]["importance"] == "HIGH"


def test_api_compare_docx():
    v1_path = SAMPLES_DIR / "attendance_v1.docx"
    v2_path = SAMPLES_DIR / "attendance_v2.docx"

    with open(v1_path, "rb") as f1, open(v2_path, "rb") as f2:
        res = client.post(
            "/api/compare",
            files={
                "old_file": ("attendance_v1.docx", f1, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                "new_file": ("attendance_v2.docx", f2, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            },
            data={"strategy": "text"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["strategy_used"] == "TextComparisonStrategy"
    assert len(data["changes"]) >= 1


def test_api_compare_pdf():
    v1_path = SAMPLES_DIR / "attendance_v1.pdf"
    v2_path = SAMPLES_DIR / "attendance_v2.pdf"

    with open(v1_path, "rb") as f1, open(v2_path, "rb") as f2:
        res = client.post(
            "/api/compare",
            files={
                "old_file": ("attendance_v1.pdf", f1, "application/pdf"),
                "new_file": ("attendance_v2.pdf", f2, "application/pdf"),
            },
            data={"strategy": "semantic"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["total_changes"] >= 1


def test_api_download_pdf_report():
    # First do a compare to populate latest cache
    v1_path = SAMPLES_DIR / "attendance_v1.txt"
    v2_path = SAMPLES_DIR / "attendance_v2.txt"

    with open(v1_path, "rb") as f1, open(v2_path, "rb") as f2:
        client.post(
            "/api/compare",
            files={
                "old_file": ("attendance_v1.txt", f1, "text/plain"),
                "new_file": ("attendance_v2.txt", f2, "text/plain"),
            },
        )

    # Now request PDF report
    report_res = client.post("/api/report/pdf")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert report_res.content.startswith(b"%PDF")

