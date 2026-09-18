import pytest
from unittest.mock import AsyncMock, MagicMock
from app.domain.suggestion import Suggestion

from app.services.attach_analysis import AttachAnalysis
from schemas.v1.pydantic_schemas import AttachAnalysisDto

pytestmark = pytest.mark.unit

@pytest.fixture
def suggestion():
    return Suggestion.create("1", "test_sender", "test_body")

@pytest.fixture
def attach_analysis_dto():
    return AttachAnalysisDto(
        ai_model="test_model",
        agent_version="1.0",
        vibe="positive",
        urgency_level="low",
        communication_style="formal",
        tags=["tag1", "tag2"],
        category="test_category",
        suggested_action="test_action",
        draft_reply="test_reply",
    )

@pytest.fixture
def suggestionRepository():
    repository = MagicMock(spec=["save", "find_by_id"])
    repository.save = AsyncMock()
    repository.find_by_id = AsyncMock()
    return repository

@pytest.mark.asyncio
async def test_attach_analysis(suggestion, attach_analysis_dto, suggestionRepository):
    suggestionRepository.save = AsyncMock(return_value=suggestion)
    suggestionRepository.find_by_id.return_value = suggestion
    attach_analysis = AttachAnalysis(suggestionRepository)

    suggestion = await attach_analysis.apply(suggestion.id, attach_analysis_dto)

    suggestionRepository.save.assert_called_once_with(suggestion)
    # In this case, since analysis was attached, the find_by_id should have been called with the message_id of the suggestion
    suggestionRepository.find_by_id.assert_called_once_with(suggestion.id)