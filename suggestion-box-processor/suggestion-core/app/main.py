from fastapi import FastAPI
from app.ports import api_router
import logging


logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Suggestion Core", version="0.1.0")
app.include_router(api_router)

