from app.infrastructure.persistence.in_memory_suggestion_repository import InMemorySuggestionRepository


_repository = InMemorySuggestionRepository()
def get_suggestion_repository():
    return _repository