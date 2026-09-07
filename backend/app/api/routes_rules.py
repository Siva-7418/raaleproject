from fastapi import APIRouter
from backend.app.models.schemas import RulesConfigSchema
from backend.app.services.rules_engine import RulesEngine

router = APIRouter(prefix="/api/rules", tags=["Rules Engine Config"])
rules_engine = RulesEngine()

@router.get("", response_model=RulesConfigSchema)
def get_rules_config():
    return rules_engine.load_config()

@router.post("", response_model=RulesConfigSchema)
def update_rules_config(new_config: RulesConfigSchema):
    return rules_engine.update_config(new_config)
