from fastapi import HTTPException, Depends
from functools import wraps
from app.exceptions.exceptions import ErrorDuringUnregistration, NoParticipantsFound, ErrorDuringRegistration, RegistrationNotFound, UserAlreadyRegistered, EventNotFound
import logging
from app.utils.cache import cache
from app.utils.auth import get_current_user

logger = logging.getLogger("app")

exception_errors = (
    ErrorDuringUnregistration,
    NoParticipantsFound,
    ErrorDuringRegistration,
    RegistrationNotFound,
    UserAlreadyRegistered,
    EventNotFound
)

ERRORS_MAPS = {
    "ErrorDuringUnregistration": ErrorDuringUnregistration,
    "NoParticipantsFound": NoParticipantsFound,
    "ErrorDuringRegistration": ErrorDuringRegistration,
    "RegistrationNotFound": RegistrationNotFound,
    "UserAlreadyRegistered": UserAlreadyRegistered,
    "EventNotFound": EventNotFound,
}

error_mapped = {
    ErrorDuringUnregistration: (401, "Error During Unregistration"),
    NoParticipantsFound: (404, "No Participants Found"),
    ErrorDuringRegistration: (401, "Error During Registration"),
    RegistrationNotFound: (404, "Registration Not Found"),
    UserAlreadyRegistered: (400, "UserAlreadyRegistered"),
    EventNotFound: (404, "Event Not Found"),
}

async def global_handle_error(exception_cls, current_user_id, log_message: str = None, cache_ttl: int = 5,):

    cache_error = f"error:{current_user_id}:{exception_cls.__name__}"

    await cache.set(cache_error, {"type": exception_cls.__name__, "message": log_message}, ttl=cache_ttl)
    
    keys_list = await cache.get(f"error_keys:{current_user_id}") or []
    if cache_error not in keys_list:
        keys_list.append(cache_error)
        await cache.set(f"error_keys:{current_user_id}", keys_list, ttl=cache_ttl)

    if log_message:
        logger.error(log_message)
    raise exception_cls()

def handle_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            self = args[0]
            current_user = getattr(self, "current_user", None)

            keys_errors = await cache.get(f"error_keys:{current_user.id}") or []
            
            for key in keys_errors:
                error_data = await cache.get(key)
                if error_data:
                    raise ERRORS_MAPS[error_data["type"]]()

            return await func(*args, **kwargs)
        except exception_errors as exc:
            status_code, message = error_mapped[type(exc)]
            logger.error(f"error: {status_code}:{type(exc).__name__}")
            raise HTTPException(status_code=status_code, detail=message)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error with intelractions {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    return wrapper