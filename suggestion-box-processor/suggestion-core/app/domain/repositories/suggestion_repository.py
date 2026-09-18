from typing import Optional, Protocol
from uuid import UUID
from app.domain.suggestion import Suggestion

class SuggestionRepository(Protocol):
    async def save(self, suggestion: Suggestion) -> Suggestion:
        ...

    async def find_by_id(self, suggestion_id: UUID) -> Optional[Suggestion]:
        ...

    async def search(self) -> list[Suggestion]:
        ...
