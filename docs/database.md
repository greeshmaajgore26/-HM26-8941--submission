# Database Design

Our system uses SQLite as the database.

## 1. Users

Stores citizens, staff and administrators.

| Field | Description |
|---|---|
| user_id | Unique user ID |
| name | User name |
| contact | Phone/email |
| role | citizen / staff / admin |

## 2. Reports

Stores civic complaints submitted by citizens.

| Field | Description |
|---|---|
| report_id | Unique complaint ID |
| user_id | Citizen who submitted the report |
| category | Garbage / pothole / streetlight / other |
| description | Description of the issue |
| before_photo | Photo submitted with the complaint |
| latitude | Complaint latitude |
| longitude | Complaint longitude |
| created_at | Date and time of submission |
| status | Current complaint status |
| priority | Complaint priority |
| risk_level | Risk of the complaint being forgotten |

## 3. Assignments

Tracks which staff member is responsible for a complaint.

| Field | Description |
|---|---|
| assignment_id | Unique assignment ID |
| report_id | Complaint being assigned |
| staff_id | Assigned staff member |
| assigned_at | Assignment time |
| accepted_at | Time staff accepted the complaint |

## 4. Cleanup Evidence

Stores evidence submitted after the civic issue has been addressed.

| Field | Description |
|---|---|
| evidence_id | Unique evidence ID |
| report_id | Related complaint |
| after_photo | Photo after the issue is addressed |
| latitude | Location where evidence was captured |
| longitude | Location where evidence was captured |
| captured_at | Date and time evidence was captured |
| verification_status | Verification result |

## 5. Status History

Maintains the complete audit trail of a complaint.

| Field | Description |
|---|---|
| history_id | Unique history ID |
| report_id | Related complaint |
| old_status | Previous status |
| new_status | New status |
| changed_at | Date and time of change |
| remarks | Additional information |

## Complaint Status Flow

OPEN → ASSIGNED → IN_PROGRESS → EVIDENCE_SUBMITTED → RESOLVED

Additional statuses:

- FLAGGED
- DUPLICATE