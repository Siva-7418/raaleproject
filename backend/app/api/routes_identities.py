from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from backend.app.db.database import get_connection
from backend.app.models.schemas import IdentitySchema

router = APIRouter(prefix="/api/identities", tags=["Identities"])

@router.get("", response_model=List[IdentitySchema])
def list_identities(
    department: Optional[str] = None,
    role_type: Optional[str] = None,
    status: Optional[str] = None
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT id, name, role_type, department, start_date, end_date, status FROM identities WHERE 1=1"
        params = []
        if department:
            query += " AND department = ?"
            params.append(department)
        if role_type:
            query += " AND role_type = ?"
            params.append(role_type)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY id ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [IdentitySchema(**dict(r)) for r in rows]
    finally:
        conn.close()
