"""
LangGraphOS compatibility endpoints (alias for LangGraph status).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from routes.langgraph_execution import get_langgraph_status


router = APIRouter(prefix="/api/v1/langgraphos", tags=["LangGraphOS"])


@router.get("/status")
def langgraphos_status(db: Session = Depends(get_db)):
    return get_langgraph_status(db)
