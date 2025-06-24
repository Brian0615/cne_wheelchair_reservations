from typing import Any, Dict

from fastapi import APIRouter

from api.src.dynamodb_service import DynamoDBService
from api.src.utils import auto_process_database_errors

db_service = DynamoDBService()
router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/get")
@auto_process_database_errors
def get(cne_year: int, setting_id: str) -> Any:
    """Get settings for a specific CNE year"""
    return db_service.get_setting(cne_year=cne_year, setting_id=setting_id)


@router.put("/update")
@auto_process_database_errors
def update(cne_year: int, settings: Dict[str, Any]) -> None:
    """Update settings for a specific CNE year"""
    db_service.update_settings(cne_year=cne_year, settings=settings)
