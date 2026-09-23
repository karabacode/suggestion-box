from typing import Annotated
from fastapi import Depends
from app.domain.repositories.suggestion_repository import SuggestionRepository
from app.dependencies import get_suggestion_repository
class SearchSuggestions:
    def __init__(
           self, 
           suggestionRepository: Annotated[SuggestionRepository, Depends(get_suggestion_repository)]
       ):
           self.suggestion_repository = suggestionRepository
    def search(self, query: str):
        # Placeholder implementation, replace with actual search logic
        return self.suggestion_repository.search()