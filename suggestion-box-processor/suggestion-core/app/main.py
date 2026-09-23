from fastapi import FastAPI
from app.ports import api_router
import logging
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Suggestion Core", version="0.1.0")
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  
    logger.error("422 Validation Error: %s | Body: %s", exc.errors(), await request.body())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

logger.info("Suggestion Core application has started.")
