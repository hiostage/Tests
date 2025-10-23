from fastapi import Query

def pagination_params(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Количество элементов на странице"),
):
    return {"page": page, "size": size}