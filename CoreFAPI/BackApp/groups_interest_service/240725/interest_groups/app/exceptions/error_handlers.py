from fastapi import HTTPException
from functools import wraps
from app.exceptions.errors import *
from app.utils.logger import logger

exceptions_errors = (
    UserAlreadyMember,
    GroupNotFound,
    CreatorNotFound,
    GroupNameAlreadyExists,
    UserNotFound,
    UserNotMemberThisGroup,
    AuthorNotFound,
    PostNotFound
)


def handler_decorator(func):
    @wraps(func)
    async def wrapper(*args,**kwargs):
        try:
            return await func(*args, **kwargs)
        except exceptions_errors as exc:
            errors_mapped ={
                UserAlreadyMember: (400, "User already member"),
                GroupNameAlreadyExists: (400, "Group name already exists"),
                UserNotMemberThisGroup: (403, "User not member this group"),
                UserNotFound: (404, "User not found"),
                GroupNotFound: (404, "Group not found"),
                CreatorNotFound: (404, "Creator not found"),
                AuthorNotFound: (404, "Authon not found"),
                PostNotFound: (404, "Post not found"),
            }
            status_code, message = errors_mapped[type(exc)]
            logger.error(f"error {status_code}: {type(exc).__name__}")
            raise HTTPException(status_code = status_code, detail=message)
        except Exception as e:
            logger.error(f"Error with intelractions with group {e}")
            raise HTTPException(status_code = 500, detail="Internal Server Error")

    return wrapper