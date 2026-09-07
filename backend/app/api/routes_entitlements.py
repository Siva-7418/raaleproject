from fastapi import APIRouter
from typing import List, Optional
from backend.app.db.database import get_connection
from backend.app.models.schemas import EntitlementSchema

router = APIRouter(prefix="/api/entitlements", tags=["Entitlements"])

@router.get("", response_model=List[EntitlementSchema])
def list_entitlements(identity_id: Optional[str] = None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT id, identity_id, resource, privilege_level, granted_date, granted_by, justification, source_system FROM entitlements"
        params = []
        if identity_id:
            query += " WHERE identity_id = ?"
            params.append(identity_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [EntitlementSchema(**dict(r)) for r in rows]
    finally:
        conn.close()
