from typing import Annotated
from uuid import UUID

from app.domain.analysis import Analysis
from app.domain.suggestion import Suggestion
from app.domain.suggestion_status import SuggestionStatusEnum
from app.domain.repositories.suggestion_repository import SuggestionRepository
from app.dependencies import get_suggestion_repository
from fastapi import Depends

class AttachAnalysis:

    def __init__(
        self,
        suggestionRepository: Annotated[SuggestionRepository, Depends(get_suggestion_repository)]
    ):
        self.suggestion_repository = suggestionRepository

    async def apply(self, suggestion_id: UUID, analysis: Analysis) -> Suggestion:
        suggestion =  await self.suggestion_repository.find_by_id(suggestion_id)
        if suggestion is None:
            raise KeyError(f"No suggestion found for suggestion_id={suggestion_id}")

        suggestion.add_analysis(analysis)
        suggestion.update_status(SuggestionStatusEnum.TRIAGED)
        return await self.suggestion_repository.save(suggestion)
