from app.clients.user_client import ExternalUserClient
from fastapi import HTTPException
import asyncio


class RecommendationService:
    def __init__(self):
        self.user_client = ExternalUserClient()

    async def get_recommendations(
        self,
        session_id: str,
        purpose_cooperation,
        priority,
        page_limit,
        total_limit,
        page,
    ):
        if (page - 1) * page_limit >= total_limit:
            return []

        current_user = await self.user_client.get_current_user(session_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        all_users = await self.user_client.get_all_users()
        all_users = [u for u in all_users if u["uuid"] != current_user["uuid"]]
        
        # Добавляем фильтрацию по purpose_cooperation
        if purpose_cooperation:
            all_users = [u for u in all_users if u.get("purpose_cooperation") == purpose_cooperation]

        user_scores = await self._calculate_scores(
            current_user, all_users, purpose_cooperation, priority
        )

        sorted_users = sorted(user_scores, key=lambda pair: pair[1], reverse=True)
        start = (page - 1) * page_limit
        end = min(start + page_limit, total_limit)

        return [user for user, _ in sorted_users[start:end]]

    async def _calculate_scores(self, current_user, all_users, purpose_cooperation, priority):
        tasks = []
        for user in all_users:
            tasks.append(
                asyncio.create_task(
                    self._score_user(current_user, user, purpose_cooperation, priority)
                )
            )
        return await asyncio.gather(*tasks)

    async def _score_user(self, current_user, user, purpose_cooperation, priority):
        score = self.calculate_relevance_score(current_user, user, purpose_cooperation, priority)
        return (user, score)

    def calculate_relevance_score(self, current_user, user, purpose_cooperation, priority) -> float:
        score = 0
        common_skills = set(current_user.get("skills", [])) & set(user.get("skills", []))
        same_location = current_user.get("location") == user.get("location")
        
        if priority == "location":
            score += 5 if same_location else 0
            score += 3 * len(common_skills)
        elif priority == "skills":
            score += 5 * len(common_skills)
            score += 2 if same_location else 0
        else:  # default case
            score += 3 if same_location else 0
            score += 2 * len(common_skills)
        
        # Небольшой бонус за совпадение ролей
        common_roles = set(current_user.get("roles", [])) & set(user.get("roles", []))
        score += 0.3 * len(common_roles)
        
        return round(score, 2)