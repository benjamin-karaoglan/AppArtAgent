"""
Prompts management module for the AppArt Agent.

This module provides versioned prompts for all LLM interactions.
Each prompt is stored as a markdown file for better readability and maintainability.

Usage:
    from app.prompts import get_prompt, get_system_prompt

    # Get a specific prompt
    prompt = get_prompt("analyze_pvag", version="v1")

    # Get system prompt for a task
    system_prompt = get_system_prompt("document_classifier", version="v1")
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent
DEFAULT_VERSION = "v1"


def get_prompt(
    prompt_name: str,
    version: str = DEFAULT_VERSION,
    **kwargs
) -> str:
    """
    Load and format a prompt from the prompts directory.

    Args:
        prompt_name: Name of the prompt file (without extension)
        version: Version folder (e.g., "v1", "v2")
        **kwargs: Variables to format into the prompt

    Returns:
        Formatted prompt string

    Example:
        prompt = get_prompt("analyze_pvag", version="v1", document_text="...")
    """
    prompt_path = PROMPTS_DIR / version / f"{prompt_name}.md"

    if not prompt_path.exists():
        # Try shared prompts
        prompt_path = PROMPTS_DIR / "shared" / f"{prompt_name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_name} (version: {version})")

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_content = f.read()

    # Remove front matter if present (lines between --- markers)
    if prompt_content.startswith("---"):
        parts = prompt_content.split("---", 2)
        if len(parts) >= 3:
            prompt_content = parts[2].strip()

    # Format with provided variables
    if kwargs:
        try:
            prompt_content = prompt_content.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable in prompt {prompt_name}: {e}")

    return prompt_content


def get_system_prompt(
    prompt_name: str,
    version: str = DEFAULT_VERSION
) -> str:
    """
    Load a system prompt from the prompts directory.

    System prompts are prefixed with 'system_' in the filename.

    Args:
        prompt_name: Name of the system prompt (without 'system_' prefix)
        version: Version folder

    Returns:
        System prompt string
    """
    return get_prompt(f"system_{prompt_name}", version=version)


def list_prompts(version: str = DEFAULT_VERSION) -> list[str]:
    """List all available prompts for a version."""
    version_dir = PROMPTS_DIR / version
    if not version_dir.exists():
        return []

    return [
        p.stem for p in version_dir.glob("*.md")
        if not p.name.startswith("_")
    ]
