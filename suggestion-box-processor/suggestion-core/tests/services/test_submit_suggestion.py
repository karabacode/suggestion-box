import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.submit_suggestion import SubmitSuggestion
from app.domain.suggestion import Suggestion

pytestmark = pytest.mark.unit

@pytest.fixture
def suggestion():
    return Suggestion.create("1", "test_sender", "test_body")

@pytest.fixture
def suggestionRepository():
    return MagicMock(spec=["save", "find_by_id"])

@pytest.mark.asyncio
async def test_submit_suggestion(suggestion, suggestionRepository):
    suggestionRepository.save = AsyncMock(return_value=suggestion)
    suggestionRepository.find_by_id.return_value = suggestion
    submit_suggestion = SubmitSuggestion(suggestionRepository)

    suggestion = await submit_suggestion.submit(suggestion)
    
    suggestionRepository.save.assert_called_once_with(suggestion)
    assert suggestion == suggestionRepository.find_by_id.return_value
