"""Utilities for calling OpenAI and converting raw dictation to structured backlog JSON.

This module handles:
- Loading system prompts and project context
- Communicating with the OpenAI API
- Processing and validating responses
- Caching to avoid duplicate API calls
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()
import time
from typing import Final

import openai

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compatibility: handle openai>=1.0 new client interface
# ---------------------------------------------------------------------------

# Determine the appropriate OpenAI client interface based on version
if hasattr(openai, "chat") and hasattr(openai.chat.completions, "create"):
    # Modern OpenAI client (>=1.0.0)
    _chat_create = openai.chat.completions.create  # type: ignore[attr-defined]
else:  
    # Legacy OpenAI client (<1.0.0)
    _chat_create = openai.ChatCompletion.create  # type: ignore[attr-defined]


# Ensure compatibility across openai package versions for error handling
try:
    # Modern OpenAI client (>=1.0.0)
    OpenAIError = openai.OpenAIError
except AttributeError:  # pragma: no cover – fallback for older versions
    # Legacy OpenAI client (<1.0.0)
    from openai.error import OpenAIError  # type: ignore

# ---------------------------------------------------------------------------
# OpenAI API client
# ---------------------------------------------------------------------------

# Cache to avoid duplicate API calls in same session
_CACHE: dict[tuple[str, str], dict] = {}

# System message placeholder - will be loaded on first use
_SYSTEM_MESSAGE = ""

# Constants
_RETRY_ATTEMPTS: Final[int] = 2

def _load_system_message() -> None:
    """Load or reload the system message.
    
    This ensures we always have the latest prompt content.
    """
    global _SYSTEM_MESSAGE
    _SYSTEM_MESSAGE = _load_prompt()

# ---------------------------------------------------------------------------
# Context and Prompt loading
# ---------------------------------------------------------------------------
def _get_readme_context(max_chars: int = 200) -> tuple[str, bool]:
    """Get meaningful content from the README.md file for context.
    
    Extracts the project title and description from the README.md file to provide
    context to the AI about the current project. This helps generate more relevant
    and accurate backlog entries.
    
    Args:
        max_chars: Maximum number of characters to include in the context
        
    Returns:
        tuple[str, bool]: A tuple containing:
            - context_string: Extracted content from README (empty if not found)
            - success_flag: True if README was successfully read, False otherwise
    """
    # Try to find README.md in several locations
    readme_paths = [
        Path(os.getcwd()) / "README.md",  # Current directory
        Path(__file__).parent.parent / "README.md",  # Project root
    ]
    
    for path in readme_paths:
        if path.exists():
            try:
                with open(str(path), "r", encoding="utf-8") as f:
                    # Read the entire file (up to a reasonable limit)
                    content = f.read(2000)  # Read more than we need to extract meaningful content
                    
                    # Extract the most meaningful parts - project name and description
                    lines = content.split('\n')
                    
                    # Get project name (usually first line, starts with #)
                    project_name = ""
                    for line in lines:
                        if line.strip().startswith('#'):
                            project_name = line.strip()
                            break
                    
                    # Get project description (usually first paragraph after title)
                    description = ""
                    description_started = False
                    for line in lines[1:]:  # Skip the first line which might be the title
                        line = line.strip()
                        if not line and not description_started:
                            continue  # Skip empty lines before description
                        if line and not line.startswith('#') and not description_started:
                            description_started = True
                            description += line + " "
                        elif description_started and not line:
                            break  # End of first paragraph
                        elif description_started:
                            description += line + " "
                    
                    # Combine and truncate if needed
                    result = f"{project_name}\n\n{description}".strip()
                    if len(result) > max_chars:
                        result = result[:max_chars-3] + "..."
                    
                    return result, True
            except Exception as e:
                logger.warning(f"Failed to read README file: {e}")
                break
    
    return "", False

def _load_prompt() -> str:
    """Load the system prompt from prompt.txt in the project root.
    
    Attempts to load the prompt from prompt.txt in the project root directory.
    Falls back to the embedded prompt if the file doesn't exist or can't be read.
    Includes README context for better AI understanding of the project.
    
    Returns:
        str: The complete system prompt with project context included
    """
    # Default embedded prompt if file not found
    _TITLE_GOOD_EXAMPLES = "Add OAuth login flow; Refactor payment adapter module; Improve CSV import performance"
    _RUBRIC = (
        "1 = Tiny tweak (≤30 min); 2 = Small feature (≤2 h); 3 = Medium feature (≤1 day); "
        "4 = Large feature (1-3 days); 5 = Complex new module (>3 days)"
    )
    
    default_prompt = (
        "You are a senior developer assisting in backlog grooming. \n\n"
        "Given a raw dictation line, respond with **ONLY** valid JSON matching this schema:\n"
        "{\n  \"title\": str,  # 5-6 word git-style imperative\n  \"difficulty\": int,  # 1-5 per rubric below\n  \"description\": str,  # cleaned full text\n  \"timestamp\": str  # ISO-8601 in UTC\n}\n\n"
        "Rules:\n"
        "- Use these good title examples as style reference: "
        f"{_TITLE_GOOD_EXAMPLES}.\n"
        "- Difficulty rubric: " + _RUBRIC + "\n"
        "- Do not add fields. Reply with JSON only."
    )
    
    # Try to find prompt.txt in several locations
    prompt_paths = [
        Path(os.getcwd()) / "prompt.txt",  # Current directory
        Path(__file__).parent.parent / "prompt.txt",  # Project root
    ]
    
    # Load prompt from file if available
    prompt_content = default_prompt
    for path in prompt_paths:
        if path.exists():
            try:
                with open(str(path), "r", encoding="utf-8") as f:
                    prompt_content = f.read().strip()
                    break
            except Exception as e:
                logger.warning(f"Failed to read prompt file: {e}")
    
    # Get README context
    readme_context, readme_found = _get_readme_context(200)
    
    # Add context section based on README availability
    context_section = ""
    if readme_found and readme_context:
        context_section = f"Project Context (extracted from README):\n{readme_context}\n\n"
    elif not readme_found:
        context_section = "Note: README.md file could not be found. Ignoring project context.\n\n"
    
    # Insert context after the first line
    lines = prompt_content.split('\n')
    if not lines:
        return prompt_content
        
    first_line = lines[0]
    rest_of_content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
    return f"{first_line}\n\n{context_section}{rest_of_content}"

# Simple in-memory cache mapping (model, prompt) -> parsed JSON response
_CACHE: dict[tuple[str, str], dict] = {}

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def sanitize_dictation(text: str) -> str:
    """Trim and normalize whitespace in the dictation string.
    
    Handles special cases where the input might be misinterpreted as meta-instructions
    rather than actual backlog items. Detects potential meta-instructions and prefixes
    them with "Backlog item:" to ensure they're processed correctly.
    
    Args:
        text: The raw dictation text from user input
        
    Returns:
        str: Sanitized dictation text ready for processing
    """
    text = text.strip()
    
    # If the input looks like a meta-instruction about the tool itself,
    # prefix it to make it clear it's a backlog item request
    meta_prefixes = [
        "be more", "make it", "you should", "can you", "please", 
        "i want", "we need", "the way you", "your", "improve"
    ]
    
    if any(text.lower().startswith(prefix) for prefix in meta_prefixes):
        text = f"Backlog item: {text}"
    
    return " ".join(text.split())


def call_openai(dictation: str, *, model: str | None = None) -> dict: 
    """Call OpenAI chat completion and return parsed JSON dict.

    Sends the dictation to OpenAI's API and processes the response into a structured
    backlog entry. Handles various edge cases including non-JSON responses and
    extracts JSON from text responses when needed.
    
    Args:
        dictation: The user's dictation text to process
        model: Optional model override (defaults to config.model)
        
    Returns:
        dict: Parsed JSON response with backlog entry fields
        
    Raises:
        ValueError: If dictation is empty or response validation fails
        OpenAIError: If API communication fails after retries
        json.JSONDecodeError: If response cannot be parsed as JSON after retries
        
    Note:
        Retries up to 2 times on API error or malformed JSON.
    """
    if not dictation.strip():
        raise ValueError("Empty dictation provided")

    # Import from config to avoid duplication
    from . import config
    model = model or config.load_config().model

    prompt_user = sanitize_dictation(dictation)

    # Quick in-memory cache to avoid duplicate API calls in same session
    _cache_key = (model, prompt_user)
    if _cache_key in _CACHE:
        logger.debug(f"Using cached response for {prompt_user[:30]}...")
        return _CACHE[_cache_key]

    # Make sure the system message is loaded before any attempts (in case it was updated)
    _load_system_message()
    
    for attempt in range(1, _RETRY_ATTEMPTS + 2):
        try:
            logger.debug(f"Attempt {attempt}: Calling OpenAI API with model {model}")
            response = _chat_create(
                model=model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": _SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt_user},
                ],
            )
            content = response.choices[0].message.content  # type: ignore[index]
            
            # Log the raw response for debugging
            logger.debug(f"Raw OpenAI response: {content}")
            
            # Clean up the content to handle potential formatting issues
            content = content.strip()
            
            # If content doesn't start with '{', try to find the JSON part
            if not content.startswith('{'):
                # Look for the first '{' character
                json_start = content.find('{')
                if json_start >= 0:
                    logger.info(f"Found JSON starting at position {json_start}, extracting JSON part")
                    content = content[json_start:]
                    
                    # Also check for proper JSON ending
                    json_end = content.rfind('}')
                    if json_end >= 0 and json_end < len(content) - 1:
                        # There's text after the last }, trim it
                        content = content[:json_end + 1]
                else:
                    # Try again with a more explicit prompt
                    if attempt < _RETRY_ATTEMPTS + 1:  # Only do this if we have retries left
                        logger.warning("No JSON found in response, retrying with explicit JSON request")
                        continue
                    else:
                        logger.error("No JSON object found in response after retries")
                        raise json.JSONDecodeError("No JSON object found in response", content, 0)
            
            try:
                data = json.loads(content)
                _validate_schema(data)
                _CACHE[_cache_key] = data
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing error: {e}")
                if attempt >= _RETRY_ATTEMPTS + 1:
                    raise
                # Otherwise, continue to retry
                
        except (OpenAIError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("OpenAI attempt %s failed: %s", attempt, exc)
            if attempt > _RETRY_ATTEMPTS:
                raise
            time.sleep(2 ** attempt)  # simple exponential back-off
    # Should never reach here
    raise RuntimeError("OpenAI call failed after retries")


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

def _validate_schema(data: dict) -> None:
    """Basic schema validation for OpenAI response.
    
    Validates that the response contains all required fields with correct types
    and that the difficulty is within the valid range (1-5).
    
    Args:
        data: The parsed JSON response from OpenAI
        
    Raises:
        ValueError: If any validation check fails
    """
    required = {"title": str, "difficulty": int, "description": str, "timestamp": str}
    for key, typ in required.items():
        if key not in data:
            raise ValueError(f"Missing key '{key}' in response JSON")
        if not isinstance(data[key], typ):
            raise ValueError(f"Field '{key}' expected {typ.__name__}, got {type(data[key]).__name__}")
    if not 1 <= data["difficulty"] <= 5:
        raise ValueError("difficulty must be between 1 and 5")
