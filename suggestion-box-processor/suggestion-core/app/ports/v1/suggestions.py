from fastapi.responses import JSONResponse
from fastapi import HTTPException, status
from google.protobuf.json_format import MessageToDict

from app.schemas.v1.submit_suggestion_dto_p2p import SubmitSuggestionDto
from app.services.search_suggestions import SearchSuggestions
from app.services.submit_suggestion import SubmitSuggestion
from app.schemas.v1.attach_analysis_dto_p2p import AttachAnalysisDto
from app.services.attach_analysis import AttachAnalysis
from app.domain.analysis import Analysis
from uuid import uuid4, UUID
from fastapi import APIRouter, Depends, Request
import logging
from typing import Annotated
from app.domain.suggestion import Suggestion
from app.dependencies import get_submit_suggestion
from google.protobuf.message import DecodeError
from app.schemas.v1 import submit_suggestion_dto_pb2

router = APIRouter(prefix="/v1/suggestions", tags=["Suggestions"])
logger = logging.getLogger(__name__)


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

async def parse_protobuf_suggestion(request: Request) -> SubmitSuggestionDto:
    """FastAPI dependency that parses binary Protobuf request body into a Pydantic DTO."""
    try:
        raw_body = await request.body()
        proto_msg = submit_suggestion_dto_pb2.SubmitSuggestionDto()
        proto_msg.ParseFromString(raw_body)
        
        # Convert Protobuf message to dict and validate against Pydantic DTO
        return SubmitSuggestionDto.model_validate(
            MessageToDict(proto_msg, preserving_proto_field_name=True)
        )
    except DecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Protobuf wire format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to validate Protobuf message schema: {str(e)}",
        )

"""
Suggestion endpoints for submitting, attaching analysis, and listing suggestions.
"""
@router.post("/", status_code=201)
async def submit_suggestion(
    submitSuggestionDto: Annotated[SubmitSuggestionDto, Depends(parse_protobuf_suggestion)],
    submitSuggestion: Annotated[SubmitSuggestion, Depends(get_submit_suggestion)],
) -> JSONResponse:
    suggestion = Suggestion.create(submitSuggestionDto.sender, submitSuggestionDto.body, submitSuggestionDto.external_reference)
    await submitSuggestion.submit(suggestion)
    return JSONResponse(content="response")

@router.post("/{suggestion_id}/analysis/")
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
    suggestions = await searchSuggestions.search("")
    return JSONResponse(content=[_suggestion_response(suggestion) for suggestion in suggestions])