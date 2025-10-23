from app.repositories import UserRepository
from fastapi import HTTPException
import asyncio


class RecommendationService:
    def __init__(self):
        self.repository = UserRepository()

    async def get_recommendations(
        self, user_id, purpose_cooperation, priority, page_limit, total_limit, page
    ):
        # Проверяем является ли page выше допустимого total_limit
        if page * page_limit - page_limit > total_limit:
            return []

        current_user = await self.repository.get_user_by_id(user_id)

        if not current_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        all_users = await self.repository.get_all_users()

        user_scores = await self._calculate_scores(
            current_user, all_users, user_id, purpose_cooperation, priority
        )

        if total_limit >= page_limit * page:
            recommended_users = [
                user
                for user, score in user_scores[
                    page * page_limit - page_limit : page * page_limit
                ]
            ]
        elif page_limit * page - total_limit >= 0:
            recommended_users = [
                user
                for user, score in user_scores[
                    page * page_limit - page_limit : total_limit
                ]
            ]

        return recommended_users

    async def _calculate_scores(
        self, current_user, all_users, user_id, purpose_cooperation, priority
    ):
        tasks = []
        for user in all_users:
            if user.id != user_id:
                task = asyncio.create_task(
                    self._score_user(current_user, user, purpose_cooperation, priority)
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks)

        return results

    async def _score_user(self, current_user, user, purpose_cooperation, priority):
        score = self.calculate_relevance_score(
            current_user, user, purpose_cooperation, priority
        )
        return (user, score)

    def calculate_relevance_score(
        self, current_user, user, purpose_cooperation, priority
    ) -> float:
        score = 0
        skills_weight = 0.3
        experience_weight = 0.1
        location_weight = 0.2

        if priority == "location":
            location_weight = 0.6

        if current_user.skills and user.skills:
            common_skills = set(current_user.skills.keys()) & set(user.skills.keys())
            # Базовая оценка по количеству общих навыков
            base_skills_score = len(common_skills) / max(
                len(current_user.skills), len(user.skills)
            )
            # Дополнительная оценка за совпадение уровней навыков
            skill_level_matches = sum(
                1
                for skill in common_skills
                if current_user.skills[skill] == user.skills[skill]
            )
            # Если есть общие навыки, рассчитываем процент совпадения уровней
            level_match_score = (
                skill_level_matches / len(common_skills) if common_skills else 0
            )

        if current_user.location and user.location:
            location_score = 0.1 if current_user.location == user.location else 0.0
            score += location_weight * location_score

            skills_score = self._get_skills_score(
                current_user,
                user,
                purpose_cooperation,
                score,
                base_skills_score,
                level_match_score,
                experience_weight,
            )
            score += skills_weight * skills_score

        return score

    def _get_skills_score(
        self,
        current_user,
        user,
        purpose_cooperation,
        score,
        base_skills_score,
        level_match_score,
        experience_weight,
    ):
        if purpose_cooperation == "exchange_experience":
            # Больше веса на совпадение уровней
            skills_score = 0.3 * base_skills_score + 0.7 * level_match_score

        elif purpose_cooperation == "job_search":
            # Для поиска работы важнее количество совпадающих навыков, чем их уровень
            skills_score = 0.8 * base_skills_score + 0.2 * level_match_score

        elif purpose_cooperation == "partnership":
            # Для партнерства важен баланс навыков и опыта
            skills_score = 0.5 * base_skills_score + 0.5 * level_match_score
            # Для партнерства желательно иметь дополняющие навыки
            complementary_skills = set(user.skills.keys()) - set(
                current_user.skills.keys()
            )
            complementary_score = (
                len(complementary_skills) / len(user.skills) if user.skills else 0
            )
            score += 0.2 * complementary_score
            # Учитываем опыт работы для партнерства
            if current_user.work_experience and user.work_experience:
                experience_score = 0.3
                score += experience_weight * experience_score
        else:
            skills_score = (
                0.7 * base_skills_score + 0.3 * level_match_score
            )  # Больше веса на количество навыков

        return skills_score
