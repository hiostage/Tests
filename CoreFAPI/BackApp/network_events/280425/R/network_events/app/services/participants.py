from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.participant import Participant
from app.schemas.participant import ParticipantCreate

async def register_participant(session: AsyncSession, user_id: int, data: ParticipantCreate) -> Participant:
    # Проверка, есть ли уже такой участник
    result = await session.execute(
        select(Participant).where(
            Participant.event_id == data.event_id,
            Participant.user_id == user_id
        )
    )
    if result.scalar_one_or_none():
        return None  # Уже зарегистрирован

    participant = Participant(event_id=data.event_id, user_id=user_id)
    session.add(participant)
    await session.commit()
    await session.refresh(participant)
    return participant
