from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database" / "civic.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row):
    return dict(row) if row else None


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():
    return "HackMysuru Civic Follow-through API is running!"


# ---------------------------------------------------------
# 1. CREATE REPORT
# POST /api/reports
# ---------------------------------------------------------

@app.route("/api/reports", methods=["POST"])
def create_report():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    required_fields = [
        "user_id",
        "category",
        "latitude",
        "longitude"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "success": False,
                "message": f"Missing field: {field}"
            }), 400

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        created_at = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO reports (
                user_id,
                category,
                description,
                before_photo,
                latitude,
                longitude,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["user_id"],
            data["category"],
            data.get("description"),
            data.get("before_photo"),
            data["latitude"],
            data["longitude"],
            created_at
        ))

        report_id = cursor.lastrowid

        # Add initial status to history
        cursor.execute("""
            INSERT INTO status_history (
                report_id,
                old_status,
                new_status,
                changed_at,
                remarks
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report_id,
            None,
            "OPEN",
            created_at,
            "Complaint created"
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Report created successfully",
            "report_id": report_id
        }), 201

    finally:
        connection.close()


# ---------------------------------------------------------
# 2. GET ALL / USER REPORTS
# GET /api/reports
# GET /api/reports?user_id=1
# ---------------------------------------------------------

@app.route("/api/reports", methods=["GET"])
def get_reports():
    user_id = request.args.get("user_id")

    connection = get_db_connection()

    try:
        if user_id:
            rows = connection.execute("""
                SELECT *
                FROM reports
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,)).fetchall()
        else:
            rows = connection.execute("""
                SELECT *
                FROM reports
                ORDER BY created_at DESC
            """).fetchall()

        reports = [row_to_dict(row) for row in rows]

        return jsonify({
            "success": True,
            "count": len(reports),
            "reports": reports
        })

    finally:
        connection.close()


# ---------------------------------------------------------
# 3. GET SINGLE REPORT
# GET /api/reports/<report_id>
# ---------------------------------------------------------

@app.route("/api/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):

    connection = get_db_connection()

    try:
        report = connection.execute("""
            SELECT *
            FROM reports
            WHERE report_id = ?
        """, (report_id,)).fetchone()

        if not report:
            return jsonify({
                "success": False,
                "message": "Report not found"
            }), 404

        return jsonify({
            "success": True,
            "report": row_to_dict(report)
        })

    finally:
        connection.close()


# ---------------------------------------------------------
# 4. UPDATE STATUS
# PUT /api/reports/<report_id>/status
# ---------------------------------------------------------

@app.route("/api/reports/<int:report_id>/status", methods=["PUT"])
def update_status(report_id):

    data = request.get_json()

    if not data or "status" not in data:
        return jsonify({
            "success": False,
            "message": "Status is required"
        }), 400

    new_status = data["status"]

    allowed_statuses = [
        "OPEN",
        "ASSIGNED",
        "IN_PROGRESS",
        "EVIDENCE_SUBMITTED",
        "RESOLVED",
        "FLAGGED",
        "DUPLICATE"
    ]

    if new_status not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Invalid status"
        }), 400

    connection = get_db_connection()

    try:
        report = connection.execute("""
            SELECT status
            FROM reports
            WHERE report_id = ?
        """, (report_id,)).fetchone()

        if not report:
            return jsonify({
                "success": False,
                "message": "Report not found"
            }), 404

        old_status = report["status"]
        changed_at = datetime.now(timezone.utc).isoformat()

        connection.execute("""
            UPDATE reports
            SET status = ?
            WHERE report_id = ?
        """, (new_status, report_id))

        connection.execute("""
            INSERT INTO status_history (
                report_id,
                old_status,
                new_status,
                changed_at,
                remarks
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report_id,
            old_status,
            new_status,
            changed_at,
            data.get("remarks")
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Status updated successfully",
            "report_id": report_id,
            "old_status": old_status,
            "new_status": new_status
        })

    finally:
        connection.close()


# ---------------------------------------------------------
# 5. GET STATUS HISTORY
# GET /api/reports/<report_id>/history
# ---------------------------------------------------------

@app.route("/api/reports/<int:report_id>/history", methods=["GET"])
def get_history(report_id):

    connection = get_db_connection()

    try:
        report = connection.execute("""
            SELECT report_id
            FROM reports
            WHERE report_id = ?
        """, (report_id,)).fetchone()

        if not report:
            return jsonify({
                "success": False,
                "message": "Report not found"
            }), 404

        rows = connection.execute("""
            SELECT *
            FROM status_history
            WHERE report_id = ?
            ORDER BY changed_at ASC
        """, (report_id,)).fetchall()

        history = [row_to_dict(row) for row in rows]

        return jsonify({
            "success": True,
            "history": history
        })

    finally:
        connection.close()


# ---------------------------------------------------------
# 6. SUBMIT CLEANUP EVIDENCE
# POST /api/reports/<report_id>/evidence
# ---------------------------------------------------------

@app.route("/api/reports/<int:report_id>/evidence", methods=["POST"])
def submit_evidence(report_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No evidence data received"
        }), 400

    required_fields = [
        "latitude",
        "longitude"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "success": False,
                "message": f"Missing field: {field}"
            }), 400

    connection = get_db_connection()

    try:
        report = connection.execute("""
            SELECT *
            FROM reports
            WHERE report_id = ?
        """, (report_id,)).fetchone()

        if not report:
            return jsonify({
                "success": False,
                "message": "Report not found"
            }), 404

        captured_at = datetime.now(timezone.utc).isoformat()

        connection.execute("""
            INSERT INTO cleanup_evidence (
                report_id,
                after_photo,
                latitude,
                longitude,
                captured_at,
                verification_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            report_id,
            data.get("after_photo"),
            data["latitude"],
            data["longitude"],
            captured_at,
            "PENDING"
        ))

        connection.execute("""
            UPDATE reports
            SET status = ?
            WHERE report_id = ?
        """, ("EVIDENCE_SUBMITTED", report_id))

        connection.execute("""
            INSERT INTO status_history (
                report_id,
                old_status,
                new_status,
                changed_at,
                remarks
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report_id,
            report["status"],
            "EVIDENCE_SUBMITTED",
            captured_at,
            "Cleanup evidence submitted"
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Cleanup evidence submitted",
            "report_id": report_id,
            "verification_status": "PENDING"
        }), 201

    finally:
        connection.close()


# ---------------------------------------------------------
# 7. BASIC RISK CHECK
# GET /api/reports/<report_id>/risk
# ---------------------------------------------------------

@app.route("/api/reports/<int:report_id>/risk", methods=["GET"])
def get_risk(report_id):

    connection = get_db_connection()

    try:
        report = connection.execute("""
            SELECT *
            FROM reports
            WHERE report_id = ?
        """, (report_id,)).fetchone()

        if not report:
            return jsonify({
                "success": False,
                "message": "Report not found"
            }), 404

        created_time = datetime.fromisoformat(
            report["created_at"].replace("Z", "+00:00")
        )

        # Handle older records that were stored without timezone information
        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)

        # Prevent negative age if an older record was created
        # using local time instead of UTC.
        age_hours = max(
            0,
            (now - created_time).total_seconds() / 3600
)

        # Simple MVP rule-based risk calculation.
        # This can later be replaced by an ML model.
        if report["status"] == "RESOLVED":
            risk = "NORMAL"
        elif age_hours >= 48:
            risk = "HIGH"
        elif age_hours >= 24:
            risk = "MEDIUM"
        else:
            risk = "NORMAL"

        connection.execute("""
            UPDATE reports
            SET risk_level = ?
            WHERE report_id = ?
        """, (risk, report_id))

        connection.commit()

        return jsonify({
            "success": True,
            "report_id": report_id,
            "age_hours": round(age_hours, 2),
            "risk_level": risk
        })

    finally:
        connection.close()


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
@app.route("/api/reports/<int:report_id>/assign", methods=["POST"])
def assign_report(report_id):
    data = request.get_json() or {}

    staff_id = data.get("staff_id")

    if not staff_id:
        return jsonify({
            "success": False,
            "message": "staff_id is required"
        }), 400

    connection = get_db_connection()

    report = connection.execute(
        "SELECT report_id, status FROM reports WHERE report_id = ?",
        (report_id,)
    ).fetchone()

    if not report:
        connection.close()
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    staff = connection.execute(
        "SELECT user_id, role FROM users WHERE user_id = ?",
        (staff_id,)
    ).fetchone()

    if not staff or staff["role"] != "staff":
        connection.close()
        return jsonify({
            "success": False,
            "message": "Invalid staff user"
        }), 400

    assigned_at = datetime.now(timezone.utc).isoformat()

    connection.execute("""
        INSERT INTO assignments
        (report_id, staff_id, assigned_at)
        VALUES (?, ?, ?)
    """, (report_id, staff_id, assigned_at))

    old_status = report["status"]

    connection.execute("""
        UPDATE reports
        SET status = 'ASSIGNED'
        WHERE report_id = ?
    """, (report_id,))

    connection.execute("""
        INSERT INTO status_history
        (report_id, old_status, new_status, changed_at, remarks)
        VALUES (?, ?, ?, ?, ?)
    """, (
        report_id,
        old_status,
        "ASSIGNED",
        assigned_at,
        f"Assigned to staff member {staff_id}"
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Report assigned successfully",
        "report_id": report_id,
        "staff_id": staff_id,
        "status": "ASSIGNED"
    })

@app.route("/api/reports/<int:report_id>/evidence/verify", methods=["PUT"])
def verify_evidence(report_id):
    data = request.get_json() or {}

    verification_status = data.get("verification_status")

    if verification_status not in ["VERIFIED", "REJECTED"]:
        return jsonify({
            "success": False,
            "message": "verification_status must be VERIFIED or REJECTED"
        }), 400

    connection = get_db_connection()

    report = connection.execute(
        "SELECT report_id, status FROM reports WHERE report_id = ?",
        (report_id,)
    ).fetchone()

    if not report:
        connection.close()
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    evidence = connection.execute("""
        SELECT evidence_id
        FROM cleanup_evidence
        WHERE report_id = ?
        ORDER BY evidence_id DESC
        LIMIT 1
    """, (report_id,)).fetchone()

    if not evidence:
        connection.close()
        return jsonify({
            "success": False,
            "message": "No cleanup evidence found"
        }), 404

    verified_at = datetime.now(timezone.utc).isoformat()

    connection.execute("""
        UPDATE cleanup_evidence
        SET verification_status = ?
        WHERE evidence_id = ?
    """, (
        verification_status,
        evidence["evidence_id"]
    ))

    old_status = report["status"]

    if verification_status == "VERIFIED":
        new_status = "RESOLVED"
        remarks = "Cleanup evidence verified successfully."
    else:
        new_status = "FLAGGED"
        remarks = "Cleanup evidence rejected and flagged for review."

    connection.execute("""
        UPDATE reports
        SET status = ?
        WHERE report_id = ?
    """, (new_status, report_id))

    connection.execute("""
        INSERT INTO status_history
        (report_id, old_status, new_status, changed_at, remarks)
        VALUES (?, ?, ?, ?, ?)
    """, (
        report_id,
        old_status,
        new_status,
        verified_at,
        remarks
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Evidence verification completed",
        "report_id": report_id,
        "verification_status": verification_status,
        "new_status": new_status
    })

if __name__ == "__main__":
    app.run(debug=True)