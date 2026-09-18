from typing import Annotated

from app.domain.suggestion import Suggestion
from app.domain.repositories.suggestion_repository import SuggestionRepository
from app.dependencies import get_suggestion_repository
from fastapi import Depends

class SubmitSuggestion:

    def __init__(
        self, 
        suggestionRepository: Annotated[SuggestionRepository, Depends(get_suggestion_repository)]
    ):
        self.suggestion_repository = suggestionRepository


    async def submit(self, suggestion: Suggestion) -> Suggestion:
        return await self.suggestion_repository.save(suggestion)
