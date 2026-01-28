from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from lightrag.api.utils_api import get_combined_auth_dependency
from lightrag.highlight import get_highlights
from lightrag.utils import logger


def create_highlight_routes(api_key: str | None = None):
    router = APIRouter(prefix="/highlight", tags=["highlight"])

    class HighlightRequest(BaseModel):
        query: str = Field(..., description="The query to find relevant highlights for")
        context: str = Field(..., description="The text content to highlight")
        threshold: float = Field(
            0.6, description="Relevance threshold (0.0 to 1.0)", ge=0.0, le=1.0
        )

    class HighlightResponse(BaseModel):
        highlighted_sentences: list[str] = Field(
            ...,
            description="List of sentences that match the query above the threshold",
        )
        sentence_probabilities: list[float] = Field(
            ..., description="Confidence scores for each highlighted sentence"
        )

    @router.post(
        "",
        response_model=HighlightResponse,
        dependencies=[Depends(get_combined_auth_dependency(api_key))]
        if api_key
        else [],
    )
    async def highlight_text(request: HighlightRequest):
        """
        Find relevant sentences in a context for a given query using semantic highlighting.
        """
        try:
            result = get_highlights(
                query=request.query,
                context=request.context,
                threshold=request.threshold,
            )
            return HighlightResponse(**result)
        except Exception as e:
            logger.error(f"Error in highlight endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
