from fastapi import APIRouter, Depends, Query
from typing import List
from app.models import UserSchema, PurposeCooperationSchema, PrioritySchema
from app.services import RecommendationService

router = APIRouter()


@router.get(
    "/",
    name="Запрос рекомендованных пользователей",
    response_model=List[UserSchema],
    tags=["Рекоммендации"],
)
async def get_user_recommendations(
    user_id: int = Query(
        ..., description="ID пользователя, которому нужны рекомендации"
    ),
    purpose_cooperation: PurposeCooperationSchema = Query(
        None, description=" Цель знакомства"
    ),
    priority: PrioritySchema = Query(None, description="Приоритетность"),
    service: RecommendationService = Depends(RecommendationService),
    page_limit: int = Query(
        10, description="Количество выдаваемых пользователей на странице"
    ),
    total_limit: int = Query(
        100, description="Общее количество выдаваемых пользователей"
    ),
    page: int = Query(1, description="Текущая страница"),
):
    """Запрос рекомендованных пользвателей на основе:

        - Скиллов

        - Опыта работы

        - Местоположения

    Имеется возможность указать цели знакомства:

        - job_search(поиск работы)

        - partnership(партнерство)

        - exchange_experience(обмен опытом)

    Имеется возможность указать приоритетность выдачи:

        - location(Пользователи из того же города становяться приоритетнее)
    """
    return await service.get_recommendations(
        user_id, purpose_cooperation, priority, page_limit, total_limit, page
    )
