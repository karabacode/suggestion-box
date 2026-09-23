from typing import Annotated

from app.domain.suggestion import Suggestion
from app.domain.repositories.suggestion_repository import SuggestionRepository
from fastapi import Depends
import logging

logger = logging.getLogger(__name__)

class SubmitSuggestion:

    def __init__(
        self, 
        suggestionRepository: SuggestionRepository
    ):
        self.suggestion_repository = suggestionRepository


    async def submit(self, suggestion: Suggestion) -> Suggestion:
        logger.info(f"Submitting suggestion: {suggestion.message}")
        return self.suggestion_repository.save(suggestion)
