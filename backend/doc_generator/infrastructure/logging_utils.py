"""
Enhanced logging utilities for better workflow visibility.

Provides decorators and helpers for clear, visually separated logging
that makes it easy to understand the workflow progress.
"""

from contextvars import ContextVar
from functools import wraps
from typing import Callable

from loguru import logger


ProgressCallback = Callable[[int, int, str, str], None]
_progress_callback: ContextVar[ProgressCallback | None] = ContextVar(
    "progress_callback",
    default=None,
)


def set_progress_callback(callback: ProgressCallback | None):
    return _progress_callback.set(callback)


def reset_progress_callback(token) -> None:
    _progress_callback.reset(token)


def _emit_progress(step_number: int, total_steps: int, node_name: str, display_name: str) -> None:
    callback = _progress_callback.get()
    if callback:
        callback(step_number, total_steps, node_name, display_name)


def resolve_step_number(state: dict, node_name: str, default: int) -> int:
    """
    Resolve the step number from state metadata, falling back to default.
    """
    metadata = state.get("metadata", {}) if isinstance(state, dict) else {}
    step_numbers = metadata.get("step_numbers", {}) if isinstance(metadata, dict) else {}
    return step_numbers.get(node_name, default)


def resolve_total_steps(state: dict, default: int) -> int:
    """
    Resolve total steps from state metadata, falling back to default.
    """
    metadata = state.get("metadata", {}) if isinstance(state, dict) else {}
    total_steps = metadata.get("total_steps") if isinstance(metadata, dict) else None
    return total_steps if isinstance(total_steps, int) and total_steps > 0 else default


# Visual separators
SEPARATOR_HEAVY = "=" * 80
SEPARATOR_LIGHT = "-" * 80
SEPARATOR_DOT = "·" * 80


def log_node_start(node_name: str, step_number: int, total_steps: int = 9) -> None:
    """
    Log the start of a workflow node with clear visual separation.
    
    Args:
        node_name: Name of the node (e.g., "detect_format")
        step_number: Current step number (1-9)
        total_steps: Total number of steps in workflow
    """
    # Convert snake_case to Title Case
    display_name = node_name.replace("_", " ").title()
    _emit_progress(step_number, total_steps, node_name, display_name)
    
    logger.opt(colors=True).info(
        f"\n{SEPARATOR_HEAVY}\n"
        f"<bold><cyan>STEP {step_number}/{total_steps}: {display_name}</cyan></bold>\n"
        f"{SEPARATOR_HEAVY}"
    )


def log_node_end(node_name: str, success: bool = True, details: str = "") -> None:
    """
    Log the end of a workflow node.
    
    Args:
        node_name: Name of the node
        success: Whether the node completed successfully
        details: Optional details to include
    """
    display_name = node_name.replace("_", " ").title()
    
    if success:
        status_icon = "✓"
        status_color = "green"
        status_text = "COMPLETED"
    else:
        status_icon = "✗"
        status_color = "red"
        status_text = "FAILED"
    
    detail_line = f"\n{details}" if details else ""
    
    logger.opt(colors=True).info(
        f"<{status_color}>{status_icon} {display_name} {status_text}</{status_color}>{detail_line}\n"
        f"{SEPARATOR_DOT}\n"
    )


def log_subsection(title: str) -> None:
    """
    Log a subsection within a node.
    
    Args:
        title: Subsection title
    """
    logger.opt(colors=True).info(
        f"{SEPARATOR_LIGHT}\n"
        f"<yellow>▸ {title}</yellow>"
    )


def log_progress(message: str, icon: str = "→") -> None:
    """
    Log a progress message within a node.
    
    Args:
        message: Progress message
        icon: Icon to use (default: →)
    """
    logger.opt(colors=True).info(f"<blue>{icon}</blue> {message}")


def log_metric(key: str, value: any, unit: str = "") -> None:
    """
    Log a metric in a consistent format.
    
    Args:
        key: Metric name
        value: Metric value
        unit: Optional unit (e.g., "chars", "ms", "MB")
    """
    unit_str = f" {unit}" if unit else ""
    logger.opt(colors=True).info(f"  <cyan>{key}:</cyan> <white>{value}{unit_str}</white>")


def log_cache_hit(cache_type: str) -> None:
    """
    Log a cache hit with special formatting.
    
    Args:
        cache_type: Type of cache (e.g., "content", "image", "request")
    """
    logger.opt(colors=True).success(
        f"<bold><green>⚡ CACHE HIT</green></bold> - {cache_type} cache reused"
    )


def log_llm_call(
    step: str,
    provider: str,
    model: str,
    input_tokens: int = None,
    output_tokens: int = None,
    duration_ms: int = None
) -> None:
    """
    Log an LLM API call with consistent formatting.
    
    Args:
        step: Step name (e.g., "content_transform")
        provider: Provider name (e.g., "gemini", "claude")
        model: Model name
        input_tokens: Input token count
        output_tokens: Output token count
        duration_ms: Duration in milliseconds
    """
    tokens_str = ""
    if input_tokens is not None and output_tokens is not None:
        tokens_str = f" ({input_tokens} → {output_tokens} tokens)"
    
    duration_str = ""
    if duration_ms is not None:
        duration_str = f" in {duration_ms/1000:.2f}s"
    
    logger.opt(colors=True).info(
        f"  <magenta>🤖 LLM Call:</magenta> {provider}/{model} - {step}{tokens_str}{duration_str}"
    )


def log_file_operation(operation: str, path: str, size_bytes: int = None) -> None:
    """
    Log a file operation.
    
    Args:
        operation: Operation type (e.g., "read", "write", "parse")
        path: File path
        size_bytes: Optional file size
    """
    size_str = ""
    if size_bytes is not None:
        if size_bytes < 1024:
            size_str = f" ({size_bytes} bytes)"
        elif size_bytes < 1024 * 1024:
            size_str = f" ({size_bytes / 1024:.1f} KB)"
        else:
            size_str = f" ({size_bytes / (1024 * 1024):.1f} MB)"
    
    logger.opt(colors=True).info(
        f"  <cyan>📄 {operation.title()}:</cyan> {path}{size_str}"
    )


def log_workflow_start(input_path: str, output_format: str) -> None:
    """
    Log the start of the entire workflow.
    
    Args:
        input_path: Input file path or URL
        output_format: Output format (pdf or pptx)
    """
    logger.opt(colors=True).info(
        f"\n\n{'=' * 80}\n"
        f"<bold><green>🚀 DOCUMENT GENERATION WORKFLOW STARTED</green></bold>\n"
        f"{'=' * 80}\n"
        f"<cyan>Input:</cyan>  {input_path}\n"
        f"<cyan>Output:</cyan> {output_format.upper()}\n"
        f"{'=' * 80}\n"
    )


def log_workflow_end(
    success: bool,
    output_path: str = None,
    errors: list = None,
    duration_seconds: float = None
) -> None:
    """
    Log the end of the entire workflow.
    
    Args:
        success: Whether workflow completed successfully
        output_path: Path to generated output file
        errors: List of errors if any
        duration_seconds: Total workflow duration
    """
    if success:
        duration_str = ""
        if duration_seconds is not None:
            duration_str = f" in {duration_seconds:.1f}s"
        
        logger.opt(colors=True).success(
            f"\n{'=' * 80}\n"
            f"<bold><green>✓ WORKFLOW COMPLETED SUCCESSFULLY</green></bold>{duration_str}\n"
            f"{'=' * 80}\n"
            f"<cyan>Output:</cyan> {output_path}\n"
            f"{'=' * 80}\n\n"
        )
    else:
        error_list = "\n".join(f"  • {err}" for err in (errors or ["Unknown error"]))
        
        logger.opt(colors=True).error(
            f"\n{'=' * 80}\n"
            f"<bold><red>✗ WORKFLOW FAILED</red></bold>\n"
            f"{'=' * 80}\n"
            f"<red>Errors:</red>\n{error_list}\n"
            f"{'=' * 80}\n\n"
        )


def log_usage_summary(
    llm_calls: int,
    image_calls: int,
    models: list,
    providers: list,
    call_details: list = None
) -> None:
    """
    Log usage summary at the end of workflow.
    
    Args:
        llm_calls: Total LLM API calls
        image_calls: Total image generation calls
        models: List of models used
        providers: List of providers used
        call_details: Detailed call information
    """
    logger.opt(colors=True).info(
        f"\n{SEPARATOR_HEAVY}\n"
        f"<bold><cyan>📊 USAGE SUMMARY</cyan></bold>\n"
        f"{SEPARATOR_HEAVY}"
    )
    
    log_metric("Total LLM Calls", llm_calls)
    log_metric("Total Image Calls", image_calls)
    log_metric("Models Used", ", ".join(models) if models else "None")
    log_metric("Providers Used", ", ".join(providers) if providers else "None")
    
    if call_details:
        logger.opt(colors=True).info(f"\n<yellow>Detailed Call Breakdown:</yellow>")
        _log_call_table(call_details)
    
    logger.info(f"{SEPARATOR_HEAVY}\n")


def _log_call_table(rows: list[dict]) -> None:
    """
    Log call details in a formatted table.
    
    Args:
        rows: List of call detail dictionaries
    """
    if not rows:
        return
    
    headers = ["Type", "Step", "Provider", "Model", "Duration", "Tokens (In→Out)"]
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    
    table_data = []
    for row in rows:
        kind = row.get("kind", "")[:10]
        step = row.get("step", "")[:20]
        provider = row.get("provider", "")[:10]
        model = row.get("model", "")[:25]
        
        duration_ms = row.get("duration_ms")
        duration = f"{duration_ms/1000:.2f}s" if duration_ms else "-"
        
        input_tokens = row.get("input_tokens")
        output_tokens = row.get("output_tokens")
        if input_tokens is not None and output_tokens is not None:
            tokens = f"{input_tokens}→{output_tokens}"
        else:
            tokens = "-"
        
        row_data = [kind, step, provider, model, duration, tokens]
        table_data.append(row_data)
        
        # Update column widths
        for i, val in enumerate(row_data):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    # Print header
    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator_line = "  ".join("-" * col_widths[i] for i in range(len(headers)))
    
    logger.info(f"\n  {header_line}")
    logger.info(f"  {separator_line}")
    
    # Print rows
    for row_data in table_data:
        row_line = "  ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row_data))
        logger.info(f"  {row_line}")


def node_logger(step_number: int, total_steps: int = 9):
    """
    Decorator for workflow nodes to add automatic logging.
    
    Args:
        step_number: Current step number
        total_steps: Total steps in workflow
    
    Usage:
        @node_logger(step_number=1)
        def detect_format_node(state: WorkflowState) -> WorkflowState:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state, *args, **kwargs):
            node_name = func.__name__.replace("_node", "")
            
            # Log start
            log_node_start(node_name, step_number, total_steps)
            
            try:
                # Execute node
                result = func(state, *args, **kwargs)
                
                # Check for errors
                errors = result.get("errors", [])
                has_new_errors = len(errors) > len(state.get("errors", []))
                
                if has_new_errors:
                    log_node_end(node_name, success=False, details=errors[-1])
                else:
                    log_node_end(node_name, success=True)
                
                return result
                
            except Exception as e:
                log_node_end(node_name, success=False, details=str(e))
                raise
        
        return wrapper
    return decorator
