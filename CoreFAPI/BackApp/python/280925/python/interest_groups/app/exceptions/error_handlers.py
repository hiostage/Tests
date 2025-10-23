from fastapi import HTTPException
from functools import wraps
from app.exceptions.errors import *
from app.utils.logger import logger
from app.utils.cache import cache

exceptions_errors = (
    UserAlreadyMember,
    GroupNotFound,
    CreatorNotFound,
    GroupNameAlreadyExists,
    UserNotFound,
    UserNotMemberThisGroup,
    AuthorNotFound,
    PostNotFound,
    CreatorOnly,
    UserNotAuthenticate
)

EXCEPTION_MAP = {
    "UserAlreadyMember": UserAlreadyMember,
    "GroupNotFound": GroupNotFound,
    "CreatorNotFound": CreatorNotFound,
    "GroupNameAlreadyExists": GroupNameAlreadyExists,
    "UserNotFound": UserNotFound,
    "UserNotMemberThisGroup": UserNotMemberThisGroup,
    "AuthorNotFound": AuthorNotFound,
    "PostNotFound": PostNotFound,
    "CreatorOnly": CreatorOnly,
    "UserNotAuthenticate": UserNotAuthenticate
}




def handler_decorator(func):
    @wraps(func)
    async def wrapper(*args,**kwargs):
        try:
            
            self = args[0]
            current_user = getattr(self, "current_user", None)
            
            if current_user is None:
                raise ValueError("current_user not found")
            
            keys_list = await cache.get(f"error_keys:{current_user.id}") or []
            for key in keys_list:
                error_data = await cache.get(key)
                if error_data:
                    raise EXCEPTION_MAP[error_data["type"]]()
                
            return await func(*args, **kwargs)
        
        except exceptions_errors as exc:
            errors_mapped ={
                UserAlreadyMember: (400, "User already member"),
                GroupNameAlreadyExists: (400, "Group name already exists"),
                UserNotMemberThisGroup: (404, "User not member this group"),
                UserNotFound: (404, "User not found"),
                GroupNotFound: (404, "Group not found"),
                CreatorNotFound: (404, "Creator not found"),
                AuthorNotFound: (404, "Author not found"),
                PostNotFound: (404, "Post not found"),
                CreatorOnly: (403, "Can only creator"),
                UserNotAuthenticate: (401, "User not authenticate")
            }
            status_code, message = errors_mapped[type(exc)]
            logger.error(f"error {status_code}: {type(exc).__name__}")
            raise HTTPException(status_code = status_code, detail=message)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error with intelractions with group {e}")
            raise HTTPException(status_code = 500, detail="Internal Server Error")

    return wrapper

