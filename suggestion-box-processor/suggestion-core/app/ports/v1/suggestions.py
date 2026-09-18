from fastapi.responses import JSONResponse

from schemas.v1.pydantic_schemas import SubmitSuggestionDto
from app.services.search_suggestions import SearchSuggestions
from app.services.submit_suggestion import SubmitSuggestion
from schemas.v1.pydantic_schemas import AttachAnalysisDto
from app.services.attach_analysis import AttachAnalysis
from app.domain.analysis import Analysis
from uuid import uuid4, UUID
from fastapi import APIRouter, Depends
from typing import Annotated
from app.domain.suggestion import Suggestion

router = APIRouter(prefix="/v1/suggestions", tags=["Suggestions"])


def _suggestion_response(suggestion: Suggestion) -> dict:
    return {
        "id": str(suggestion.id),
        "external_reference": suggestion.external_reference,
        "status": suggestion.status.status.value,
        "message": {
            "sender": suggestion.message.sender,
            "body": suggestion.message.body,
        },
        "analyses": [
            {
                "id": analysis.id,
                "ai_model": analysis.ai_model,
                "agent_version": analysis.agent_version,
                "category": analysis.category,
                "suggested_action": analysis.suggested_action,
                "draft_reply": analysis.draft_reply,
            }
            for analysis in suggestion.analyses
        ],
    }


@router.post("/", status_code=201)
async def submit_suggestion(
    suggestionDto: SubmitSuggestionDto, submitSuggestion: Annotated[SubmitSuggestion, Depends()]
) -> JSONResponse:
    suggestion = Suggestion.create(suggestionDto.sender, suggestionDto.body, suggestionDto.external_reference)
    await submitSuggestion.submit(suggestion)
    return JSONResponse(content=_suggestion_response(suggestion))

@router.post("/{suggestion_id}/analysis")
async def attach_analysis(
    suggestion_id: UUID,
    analysisDto: AttachAnalysisDto,
    attachAnalysis: Annotated[AttachAnalysis, Depends()],
) -> JSONResponse:
    analysis = Analysis.create(
        str(uuid4()),
        str(suggestion_id),
        analysisDto.ai_model,
        analysisDto.agent_version,
        vibe=analysisDto.vibe,
        urgency_level=analysisDto.urgency_level,
        communication_style=analysisDto.communication_style,
        tags=analysisDto.tags,
        category=analysisDto.category,
        suggested_action=analysisDto.suggested_action,
        draft_reply=analysisDto.draft_reply,
    )
    result = await attachAnalysis.apply(suggestion_id, analysis)
    return JSONResponse(content=_suggestion_response(result))

@router.get("/")
async def list_suggestions(searchSuggestions: Annotated[SearchSuggestions, Depends()]) -> JSONResponse:
    # Placeholder implementation, replace with actual retrieval logic
    suggestions =  await searchSuggestions.search("")
    return JSONResponse(content=[_suggestion_response(suggestion) for suggestion in suggestions])