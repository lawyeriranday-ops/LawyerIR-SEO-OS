from fastapi import HTTPException


def handle_service_error(exc: ValueError) -> None:
    message = str(exc)
    if "already" in message.lower():
        raise HTTPException(status_code=409, detail=message) from exc
    if "not found" in message.lower():
        raise HTTPException(status_code=404, detail=message) from exc
    raise HTTPException(status_code=422, detail=message) from exc
