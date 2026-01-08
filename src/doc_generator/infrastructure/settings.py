"""
Application settings with Pydantic validation.

Provides centralized configuration loading from config/settings.yaml with
type validation and environment variable support.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings


class PdfPaletteSettings(BaseSettings):
    """Color palette settings for PDF generation."""

    ink: str = "#1C1C1C"
    muted: str = "#4A4A4A"
    paper: str = "#F6F1E7"
    panel: str = "#FFFDF8"
    accent: str = "#D76B38"
    teal: str = "#1E5D5A"
    line: str = "#E2D7C9"
    code: str = "#F2EEE7"
    table: str = "#F8F4ED"


class PdfMarginSettings(BaseSettings):
    """PDF margin settings."""

    top: int = 72
    bottom: int = 18
    left: int = 72
    right: int = 72


class PdfSettings(BaseSettings):
    """PDF generation settings."""

    page_size: str = "letter"
    margin: PdfMarginSettings = Field(default_factory=PdfMarginSettings)
    palette: PdfPaletteSettings = Field(default_factory=PdfPaletteSettings)
    image_cache_dir: str = "src/output/pdf_images"


class PptxThemeSettings(BaseSettings):
    """PPTX theme color settings."""

    background: str = "#FFFFFF"
    text: str = "#1C1C1C"
    accent: str = "#D76B38"
    secondary: str = "#1E5D5A"


class PptxSettings(BaseSettings):
    """PPTX generation settings."""

    layout: str = "LAYOUT_16x9"
    slide_width: int = 960
    slide_height: int = 540
    theme: PptxThemeSettings = Field(default_factory=PptxThemeSettings)


class DoclingSettings(BaseSettings):
    """Docling parser settings."""

    ocr_enabled: bool = True
    table_structure_extraction: bool = True


class WebParserSettings(BaseSettings):
    """Web parser settings."""

    timeout: int = 10
    user_agent: str = "doc-generator/0.1.0"


class ParserSettings(BaseSettings):
    """Parser configuration settings."""

    docling: DoclingSettings = Field(default_factory=DoclingSettings)
    web: WebParserSettings = Field(default_factory=WebParserSettings)


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )


class GeneratorSettings(BaseSettings):
    """Generator-specific settings."""

    input_dir: Path = Path("src/data")
    output_dir: Path = Path("src/output")
    visuals_dir: Path = Path("src/output/visuals")
    temp_dir: Path = Path("src/output/temp")
    default_output_format: str = "pdf"
    max_retries: int = Field(default=3, ge=1, le=10)


class LlmSettings(BaseSettings):
    """LLM service settings."""

    model: str = "gpt-4o-mini"
    max_summary_points: int = 5
    max_slides: int = 10
    max_tokens_summary: int = 500
    max_tokens_slides: int = 2000
    temperature_summary: float = 0.3
    temperature_slides: float = 0.4

    # Claude API settings for SVG generation
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4000
    claude_temperature: float = 0.3
    use_claude_for_visuals: bool = True


class SvgSettings(BaseSettings):
    """SVG generation settings."""

    default_width: int = 800
    default_height: int = 500
    chart_colors: list[str] = Field(
        default=[
            "#1E5D5A",
            "#D76B38",
            "#2E86AB",
            "#A23B72",
            "#F18F01",
            "#C73E1D",
            "#3A7CA5",
            "#5C946E",
        ]
    )
    layer_colors: dict[str, str] = Field(
        default={
            "frontend": "#2E86AB",
            "backend": "#1E5D5A",
            "database": "#A23B72",
            "external": "#D76B38",
            "infrastructure": "#5C946E",
            "default": "#3A7CA5",
        }
    )


class Settings(BaseSettings):
    """
    Main application settings.

    Loads configuration from config/settings.yaml and validates with Pydantic.
    Environment variables can override YAML values (prefix: DOC_GENERATOR_).
    """

    generator: GeneratorSettings = Field(default_factory=GeneratorSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    pdf: PdfSettings = Field(default_factory=PdfSettings)
    pptx: PptxSettings = Field(default_factory=PptxSettings)
    parsers: ParserSettings = Field(default_factory=ParserSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)
    svg: SvgSettings = Field(default_factory=SvgSettings)

    class Config:
        env_prefix = "DOC_GENERATOR_"
        env_nested_delimiter = "__"


def _find_config_file() -> Optional[Path]:
    """
    Find the configuration file.

    Searches in common locations for config/settings.yaml.

    Returns:
        Path to config file or None if not found
    """
    search_paths = [
        Path("config/settings.yaml"),
        Path("../config/settings.yaml"),
        Path(__file__).parent.parent.parent.parent / "config" / "settings.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return path.resolve()

    return None


def _load_yaml_config() -> dict:
    """
    Load configuration from YAML file.

    Returns:
        Configuration dictionary or empty dict if file not found
    """
    config_path = _find_config_file()

    if config_path is None:
        logger.warning("Configuration file not found, using defaults")
        return {}

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
            logger.debug(f"Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return {}


def _merge_config(yaml_config: dict) -> dict:
    """
    Merge YAML configuration into nested settings format.

    Args:
        yaml_config: Raw YAML configuration dictionary

    Returns:
        Merged configuration ready for Pydantic
    """
    # Map YAML keys to settings structure
    merged = {}

    if "generator" in yaml_config:
        merged["generator"] = yaml_config["generator"]

    if "logging" in yaml_config:
        merged["logging"] = yaml_config["logging"]

    if "pdf" in yaml_config:
        merged["pdf"] = yaml_config["pdf"]

    if "pptx" in yaml_config:
        merged["pptx"] = yaml_config["pptx"]

    if "parsers" in yaml_config:
        merged["parsers"] = yaml_config["parsers"]

    if "llm" in yaml_config:
        merged["llm"] = yaml_config["llm"]

    if "svg" in yaml_config:
        merged["svg"] = yaml_config["svg"]

    return merged


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings (cached).

    Loads from config/settings.yaml and validates with Pydantic.
    Results are cached for performance.

    Returns:
        Validated Settings instance
    """
    yaml_config = _load_yaml_config()
    merged_config = _merge_config(yaml_config)

    try:
        settings = Settings(**merged_config)
        logger.info("Settings loaded successfully")
        return settings
    except Exception as e:
        logger.error(f"Failed to validate settings: {e}")
        logger.info("Using default settings")
        return Settings()


# Convenience function for accessing settings
settings = get_settings()
