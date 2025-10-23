import httpx


SERVICE_URL = "http://value_app:8000"


async def get_val_from_service(val_id: int):
    url = f"{SERVICE_URL}/get-by-id/{val_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise Exception("Value not found")
    
    return response.json()