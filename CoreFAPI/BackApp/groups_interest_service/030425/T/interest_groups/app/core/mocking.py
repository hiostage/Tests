from functools import wraps
import os
import json
from typing import Optional

def mock_if_enabled(mock_data: Optional[str] = None):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            if os.getenv("MOCK_SERVICES", "False").lower() == "true":
                if mock_data:
                    return json.loads(mock_data)
                return {"status": "mocked_default_response"}
            return await f(*args, **kwargs)
        return wrapper
    return decorator