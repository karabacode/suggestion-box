from threading import Lock
from typing import Optional
from uuid import UUID

import logging

from app.domain.suggestion import Suggestion
from app.domain.repositories.suggestion_repository import SuggestionRepository

"""
Process-local stub repository. Not durable; replace with a real datastore adapter.
"""
class InMemorySuggestionRepository(SuggestionRepository):
    def __init__(self) -> None:
        self._by_id: dict[UUID, Suggestion] = {}
        self._lock = Lock()
        self._logger = logging.getLogger(__name__)

    async def save(self, suggestion: Suggestion) -> Suggestion:
        with self._lock:
            self._by_id[suggestion.id] = suggestion
        self._logger.info("Saved suggestion with ID %s", suggestion.id)
        return suggestion

    async def find_by_id(self, suggestion_id: UUID) -> Optional[Suggestion]:
        with self._lock:
            return self._by_id.get(suggestion_id)

    async def search(self) -> list[Suggestion]:
        with self._lock:
            return list(self._by_id.values())
