from fastapi import APIRouter, Depends, Cookie, Query
from typing import List
from app.models import UserSchema, PurposeCooperationSchema, PrioritySchema
from app.repositories import RecommendationService

router = APIRouter()

@router.get(
    "/",
    response_model=List[UserSchema],
    tags=["Рекоммендации"],
)
async def get_user_recommendations(
    session_id: str = Cookie(..., alias="sessionId"),
    purpose_cooperation: PurposeCooperationSchema = Query(None),
    priority: PrioritySchema = Query(None),
    page_limit: int = Query(10),
    total_limit: int = Query(100),
    page: int = Query(1),
    service: RecommendationService = Depends(RecommendationService),
):
    return await service.get_recommendations(
        session_id, purpose_cooperation, priority, page_limit, total_limit, page
    )
