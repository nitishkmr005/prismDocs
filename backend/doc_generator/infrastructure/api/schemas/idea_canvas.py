"""Pydantic request and response models for Idea Canvas."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .requests import Provider


class CanvasTemplate(str, Enum):
    """Pre-defined canvas templates for quick start."""

    STARTUP = "startup"
    WEB_APP = "web_app"
    AI_AGENT = "ai_agent"
    PROJECT_SPEC = "project_spec"
    TECH_STACK = "tech_stack"
    CUSTOM = "custom"
    # Developer-focused templates
    IMPLEMENT_FEATURE = "implement_feature"
    SOLVE_PROBLEM = "solve_problem"
    PERFORMANCE = "performance"
    SCALING = "scaling"
    SECURITY_REVIEW = "security_review"
    CODE_ARCHITECTURE = "code_architecture"


class QuestionType(str, Enum):
    """Types of questions that can be asked."""

    SINGLE_CHOICE = "single_choice"  # Pick one option
    MULTI_CHOICE = "multi_choice"  # Pick multiple options
    TEXT_INPUT = "text_input"  # Free text response
    APPROACH = "approach"  # Trade-off comparison (2-3 options with pros/cons)


class CanvasNodeType(str, Enum):
    """Types of nodes in the canvas."""

    ROOT = "root"  # Starting idea
    QUESTION = "question"  # Question asked
    ANSWER = "answer"  # User's answer
    APPROACH = "approach"  # Trade-off decision


# Request Models


class StartCanvasRequest(BaseModel):
    """Request to start a new canvas session."""

    template: CanvasTemplate = CanvasTemplate.CUSTOM
    idea: str = Field(
        description="The user's idea or topic to explore",
        min_length=1,
        max_length=2000,
    )
    provider: Provider = Provider.GEMINI
    model: str = "gemini-2.5-flash-lite"

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "template": "web_app",
                    "idea": "I want to build a task management app with team collaboration features",
                    "provider": "gemini",
                    "model": "gemini-2.5-flash-lite",
                }
            ]
        }
    )


class AnswerRequest(BaseModel):
    """Request to submit an answer to a question."""

    session_id: str = Field(description="Canvas session ID")
    question_id: str = Field(description="ID of the question being answered")
    answer: str | list[str] = Field(
        description="User's answer (string or list for multi-choice)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "sess_abc123",
                    "question_id": "q_1",
                    "answer": "SaaS Dashboard",
                }
            ]
        }
    )


# Response/Event Models


class QuestionOption(BaseModel):
    """An option for a multiple choice question."""

    id: str
    label: str
    description: str | None = None
    recommended: bool = False


class ApproachOption(BaseModel):
    """An approach option with trade-offs."""

    id: str
    title: str
    description: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    recommended: bool = False


class CanvasQuestion(BaseModel):
    """A question to display to the user."""

    id: str
    question: str
    type: QuestionType
    options: list[QuestionOption] = Field(default_factory=list)
    approaches: list[ApproachOption] = Field(default_factory=list)
    allow_skip: bool = True
    context: str | None = None  # Additional context about the question


class CanvasNode(BaseModel):
    """A node in the canvas tree."""

    id: str
    type: CanvasNodeType
    label: str
    description: str | None = None
    children: list["CanvasNode"] = Field(default_factory=list)
    # For answer nodes: store all available options and which was selected
    options: list[QuestionOption] = Field(default_factory=list)
    selected_option_id: str | None = None


class CanvasState(BaseModel):
    """Current state of the canvas."""

    session_id: str
    idea: str
    template: CanvasTemplate
    nodes: CanvasNode
    question_count: int = 0
    is_complete: bool = False


# SSE Event Models


class CanvasQuestionEvent(BaseModel):
    """Event containing a new question for the user."""

    type: Literal["question"] = "question"
    question: CanvasQuestion
    canvas: CanvasState


class CanvasProgressEvent(BaseModel):
    """Progress event during canvas operations."""

    type: Literal["progress"] = "progress"
    message: str


class CanvasCompleteEvent(BaseModel):
    """Event indicating the exploration is complete."""

    type: Literal["suggest_complete"] = "suggest_complete"
    message: str
    canvas: CanvasState


class CanvasErrorEvent(BaseModel):
    """Error event."""

    type: Literal["error"] = "error"
    message: str
    code: str | None = None


class CanvasReadyEvent(BaseModel):
    """Event indicating the session is ready."""

    type: Literal["ready"] = "ready"
    session_id: str
    canvas: CanvasState


class GenerateReportRequest(BaseModel):
    """Request to generate a report from a canvas session."""

    session_id: str = Field(description="Canvas session ID")
    output_format: Literal["pdf", "markdown", "both"] = "both"

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "sess_abc123",
                    "output_format": "both",
                }
            ]
        }
    )


class GenerateReportResponse(BaseModel):
    """Response with generated report download URLs."""

    session_id: str
    title: str
    pdf_url: str | None = None
    pdf_base64: str | None = None  # Base64-encoded PDF data
    image_base64: str | None = None  # Base64-encoded summary image (PNG)
    image_format: str | None = None
    markdown_url: str | None = None
    markdown_content: str | None = None


# Approach Generation Schemas


class ApproachTask(BaseModel):
    """A task within an approach."""

    id: str
    name: str
    description: str
    tech_stack: str = Field(alias="techStack")
    complexity: Literal["Low", "Medium", "High"]

    model_config = ConfigDict(populate_by_name=True)


class Approach(BaseModel):
    """A single implementation approach."""

    id: str
    name: str
    mermaid_code: str = Field(alias="mermaidCode")
    tasks: list[ApproachTask]

    model_config = ConfigDict(populate_by_name=True)


class GenerateApproachesRequest(BaseModel):
    """Request to generate implementation approaches."""

    session_id: str


class GenerateApproachesResponse(BaseModel):
    """Response with 4 implementation approaches."""

    approaches: list[Approach]


class RefineApproachRequest(BaseModel):
    """Request to refine a specific approach."""

    session_id: str
    approach_index: int
    element_id: str
    element_type: Literal["diagram", "task"]
    refinement_answer: str
    current_approach: Approach


class RefineApproachResponse(BaseModel):
    """Response with the refined approach."""

    approach: Approach
