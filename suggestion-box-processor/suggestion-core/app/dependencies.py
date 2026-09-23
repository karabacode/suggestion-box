from app.services.submit_suggestion import SubmitSuggestion

submit_suggestion = None

from app.infrastructure.persistence.in_memory_suggestion_repository import InMemorySuggestionRepository
from app.domain.repositories.suggestion_repository import SuggestionRepository

_repository = InMemorySuggestionRepository()
def get_suggestion_repository() -> SuggestionRepository:
    return _repository

def get_submit_suggestion():
    global submit_suggestion
    if submit_suggestion is None:
        submit_suggestion = SubmitSuggestion(get_suggestion_repository())
    return submit_suggestion