"""
Application layer for document generator.

This layer contains:
- nodes/                  - LangGraph workflow nodes
- parsers/                - Content parsers for various file formats
- unified_workflow.py     - Unified workflow for all content types
- unified_state.py        - State model for unified workflow
- checkpoint_manager.py   - Session-based checkpointing for state reuse
"""

# Unified workflow exports
from .unified_workflow import (
    build_unified_workflow,
    run_unified_workflow,
    run_unified_workflow_async,
    # Checkpointed workflow functions
    run_unified_workflow_with_session,
    run_unified_workflow_async_with_session,
    get_session_info,
)
from .unified_state import (
    UnifiedWorkflowState,
    get_output_branch,
    is_document_type,
    requires_content_extraction,
    requires_gemini_key,
)

# Checkpoint manager
from .checkpoint_manager import (
    CheckpointManager,
    get_checkpoint_manager,
)

__all__ = [
    # Unified workflow (no checkpointing)
    "build_unified_workflow",
    "run_unified_workflow",
    "run_unified_workflow_async",
    # Unified workflow (with checkpointing)
    "run_unified_workflow_with_session",
    "run_unified_workflow_async_with_session",
    "get_session_info",
    # State model
    "UnifiedWorkflowState",
    "get_output_branch",
    "is_document_type",
    "requires_content_extraction",
    "requires_gemini_key",
    # Checkpoint manager
    "CheckpointManager",
    "get_checkpoint_manager",
]
