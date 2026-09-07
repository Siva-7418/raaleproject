import sqlite3
import random
import uuid
import datetime
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from backend.app.db.database import get_connection, init_db

DEPARTMENTS = ["Computer Science", "Biology", "Finance", "Medicine", "Registrar"]
COLLAPSED_DEPT = "Astronomy"
ROLE_TYPES = ["student", "faculty", "alumni", "temp_researcher"]

RESOURCES = [
    "student_records",
    "finance_system",
    "research_data_vault",
    "library_catalog",
    "email_portal",
    "grading_portal",
    "hpc_cluster",
    "payroll_system",
    "astronomy_telescope_ctrl"
]

FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Casey", "Avery", "Jamie", "Dakota", "Reese", "Quinn", "Skyler", "Rowan", "Hayden", "Emerson", "Finley", "Sawyer"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

def random_date(d1, d2):
    min_d = min(d1, d2)
    max_d = max(d1, d2)
    days_ago = random.randint(min_d, max_d)
    today = datetime.datetime.now(datetime.timezone.utc)
    return (today - datetime.timedelta(days=days_ago)).isoformat()

def generate_seed_data(db_file=None):
    init_db(db_file)
    conn = get_connection(db_file)
    cursor = conn.cursor()

    random.seed(42)

    identities = []
    entitlements = []
    usage_events = []

    identity_counter = 1000

    for i in range(150):
        identity_counter += 1
        id_str = f"USER-{identity_counter}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        role_type = random.choices(ROLE_TYPES, weights=[0.40, 0.25, 0.20, 0.15])[0]
        dept = random.choice(DEPARTMENTS)
        
        start_days_ago = random.randint(180, 1000)
        start_date = random_date(start_days_ago, start_days_ago)
        
        status = "active"
        end_date = None
        if role_type in ["alumni", "temp_researcher"] and random.random() < 0.35:
            status = "offboarded"
            end_days_ago = random.randint(10, 150)
            end_date = random_date(end_days_ago, end_days_ago)

        identities.append((id_str, name, role_type, dept, start_date, end_date, status))

    # Add Edge Cases
    id_edge1 = "USER-EDGE-01"
    identities.append((id_edge1, "Dr. Alice Vance (New Researcher)", "temp_researcher", "Biology", random_date(10, 10), None, "active"))
    ent_edge1 = ("ENT-EDGE-01", id_edge1, "research_data_vault", "write", random_date(5, 5), "Admin-01", "Lab Project BioX", "primary_iam")
    entitlements.append(ent_edge1)

    id_edge2 = "USER-EDGE-02"
    identities.append((id_edge2, "Bob Miller (Offboarded Alumni)", "alumni", "Computer Science", random_date(400, 400), random_date(40, 40), "offboarded"))
    ent_edge2 = ("ENT-EDGE-02", id_edge2, "student_records", "admin", random_date(300, 300), "Admin-02", "CS Dept Admin", "primary_iam")
    entitlements.append(ent_edge2)
    usage_events.append((f"LOG-{uuid.uuid4().hex[:8]}", "ENT-EDGE-02", random_date(2, 2), "query"))

    id_edge4 = "USER-EDGE-04"
    identities.append((id_edge4, "Dr. Carl Sagan (Solo Astronomer)", "faculty", COLLAPSED_DEPT, random_date(500, 500), None, "active"))
    ent_edge4 = ("ENT-EDGE-04", id_edge4, "astronomy_telescope_ctrl", "admin", random_date(400, 400), "Chair-Astronomy", "Telescope Operations", "primary_iam")
    entitlements.append(ent_edge4)
    usage_events.append((f"LOG-{uuid.uuid4().hex[:8]}", "ENT-EDGE-04", random_date(5, 5), "control"))

    id_edge5 = "USER-EDGE-05"
    identities.append((id_edge5, "Diana Prince (Multi-System User)", "faculty", "Computer Science", random_date(300, 300), None, "active"))
    ent_edge5_a = ("ENT-EDGE-05A", id_edge5, "finance_system", "write", random_date(200, 200), "IAM-Sync", "Grant Admin", "primary_iam")
    ent_edge5_b = ("ENT-EDGE-05B", id_edge5, "finance_system", "admin", random_date(180, 180), "Legacy-HR", "Legacy HR Import", "legacy_hr")
    entitlements.append(ent_edge5_a)
    entitlements.append(ent_edge5_b)
    usage_events.append((f"LOG-{uuid.uuid4().hex[:8]}", "ENT-EDGE-05A", random_date(10, 10), "write_report"))

    ent_counter = 5000
    for ident in identities:
        id_str, name, role_type, dept, start_date, end_date, status = ident
        if id_str.startswith("USER-EDGE"):
            continue

        if role_type == "student":
            resources_assigned = [("email_portal", "read"), ("library_catalog", "read")]
            if random.random() < 0.20:
                resources_assigned.append(("hpc_cluster", "read"))
        elif role_type == "faculty":
            resources_assigned = [("email_portal", "read"), ("grading_portal", "write"), ("library_catalog", "read")]
            if random.random() < 0.40:
                resources_assigned.append(("research_data_vault", "write"))
            if random.random() < 0.15:
                resources_assigned.append(("finance_system", "admin"))
        elif role_type == "alumni":
            resources_assigned = [("email_portal", "read"), ("library_catalog", "read")]
            if status == "offboarded" and random.random() < 0.30:
                resources_assigned.append(("student_records", "write"))
        elif role_type == "temp_researcher":
            resources_assigned = [("research_data_vault", "read"), ("hpc_cluster", "execute")]
            if random.random() < 0.25:
                resources_assigned.append(("finance_system", "read"))

        for res, priv in resources_assigned:
            ent_counter += 1
            ent_id = f"ENT-{ent_counter}"
            grant_days = random.randint(30, 300)
            granted_date = random_date(grant_days, grant_days)
            granted_by = "DeptHead-Auto"
            justification = f"Standard assignment for {role_type} in {dept}" if random.random() > 0.15 else None
            
            entitlements.append((ent_id, id_str, res, priv, granted_date, granted_by, justification, "primary_iam"))

            # Graduated usage scenarios: recent (1-20d), moderate (40-75d), old (100-200d), no usage
            usage_scenario = random.choices(["recent", "moderate", "old", "no_usage"], weights=[0.45, 0.25, 0.20, 0.10])[0]

            if usage_scenario == "recent":
                for _ in range(random.randint(2, 6)):
                    usage_events.append((f"LOG-{uuid.uuid4().hex[:8]}", ent_id, random_date(1, 20), "access"))
            elif usage_scenario == "moderate":
                for _ in range(random.randint(1, 3)):
                    usage_events.append((f"LOG-{uuid.uuid4().hex[:8]}", ent_id, random_date(40, 75), "access"))
            elif usage_scenario == "old":
                for _ in range(random.randint(1, 3)):
                    usage_events.append((f"LOG-{uuid.uuid4().hex[:8]}", ent_id, random_date(100, 200), "access"))

    cursor.executemany("INSERT INTO identities VALUES (?,?,?,?,?,?,?)", identities)
    cursor.executemany("INSERT INTO entitlements VALUES (?,?,?,?,?,?,?,?)", entitlements)
    cursor.executemany("INSERT INTO usage_events VALUES (?,?,?,?)", usage_events)

    conn.commit()

    cursor.execute("""
        SELECT role_type, department, resource, privilege_level, COUNT(DISTINCT identity_id)
        FROM entitlements
        JOIN identities ON entitlements.identity_id = identities.id
        WHERE identities.status = 'active'
        GROUP BY role_type, department, resource, privilege_level
    """)
    holding_counts = cursor.fetchall()

    cursor.execute("""
        SELECT role_type, department, COUNT(DISTINCT id)
        FROM identities
        WHERE status = 'active'
        GROUP BY role_type, department
    """)
    peer_totals = {(r[0], r[1]): r[2] for r in cursor.fetchall()}

    baseline_rows = []
    for row in holding_counts:
        r_type, dept, res, priv, holding_cnt = row
        total_p = peer_totals.get((r_type, dept), holding_cnt)
        pct = round((holding_cnt / total_p) * 100.0, 2) if total_p > 0 else 0.0
        is_collapsed = 1 if total_p <= 2 else 0
        baseline_rows.append((r_type, dept, res, priv, total_p, holding_cnt, pct, is_collapsed))

    cursor.executemany("""
        INSERT INTO peer_role_baselines (role_type, department, resource, privilege_level, total_peers, peers_holding_count, peer_holding_pct, is_collapsed)
        VALUES (?,?,?,?,?,?,?,?)
    """, baseline_rows)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    generate_seed_data()
