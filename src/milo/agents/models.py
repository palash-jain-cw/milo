"""Pydantic models for agent responses."""

from pydantic import BaseModel, Field
from typing import Literal


class IntentClassificationResponse(BaseModel):
    """Response model for the router agent's intent classification."""

    route: Literal["conversational", "agent", "clarify"] = Field(
        ..., description="The route to take based on the user's message"
    )
    reasoning: str = Field(
        ..., description="A brief explanation of why this route was chosen"
    )


class ClarifierResponse(BaseModel):
    """Response model for the clarifier agent's question generation."""

    clarifying_question: str = Field(
        ...,
        description="A short, natural question to ask the user to resolve ambiguity.",
    )
    reasoning: str = Field(
        ...,
        description="A concise reasoning for why clarification is needed or what was ambiguous.",
    )


class ClarificationResolutionResponse(BaseModel):
    """Response model for resolving user's clarification into explicit message."""

    resolution: str = Field(
        ...,
        description="A clear, explicit message that the task manager can understand and route normally.",
    )

