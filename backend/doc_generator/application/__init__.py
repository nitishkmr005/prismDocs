"""
Application layer for document generator.

This layer contains:
- services/  - Application services for orchestration
- workflow/  - LangGraph workflow for document generation
  - nodes/   - Workflow nodes
- parsers/   - Content parsers (legacy, will be removed)
- graph_workflow.py - Main workflow (legacy, use workflow/)
"""

# Re-export commonly used items for backward compatibility
from .graph_workflow import run_workflow

__all__ = [
    "run_workflow",
]
