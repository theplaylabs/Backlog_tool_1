"""Tests for README context inclusion in the OpenAI prompt."""
import os
from pathlib import Path
from unittest import mock

import pytest

from backlog_cli.openai_client import _get_readme_context, _load_prompt


# Helper class for mocking OpenAI responses
class MockChoice:
    """Mock class for OpenAI API response choices."""
    def __init__(self, content):
        self.message = mock.MagicMock(content=content)


def test_get_readme_context():
    """Test that README context is correctly extracted."""
    test_content = "# Test README\n\nThis is a test README file with more than 200 characters. " + "x" * 200
    
    # Mock the file operations
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("builtins.open", mock.mock_open(read_data=test_content)):
            context, success = _get_readme_context(200)
            
            # Should extract meaningful content
            assert success is True
            assert "# Test README" in context
            assert "This is a test README file" in context
            assert len(context) <= 200


def test_readme_context_in_prompt():
    """Test that README context is included in the prompt."""
    mock_readme = "# BCKL - Backlog CLI\n\nA tool for managing backlog items."
    
    # Mock the README context function
    with mock.patch("backlog_cli.openai_client._get_readme_context", return_value=(mock_readme, True)):
        prompt = _load_prompt()
        
        # Check that context is included
        assert "Project Context" in prompt
        assert mock_readme in prompt


def test_missing_readme_handled_gracefully():
    """Test that missing README is handled gracefully."""
    # Mock the README context function to return empty string and False (no README found)
    with mock.patch("backlog_cli.openai_client._get_readme_context", return_value=("", False)):
        prompt = _load_prompt()
        
        # Check that prompt still works without README context
        assert "You are a senior developer" in prompt
        assert "README.md file could not be found" in prompt


def test_json_extraction_from_response():
    """Test that JSON is correctly extracted from responses with text before the JSON."""
    from backlog_cli.openai_client import call_openai
    
    # Mock the OpenAI response to include text before the JSON
    mock_response_text = "I'm thinking about your request... Here's the result:\n{\"title\": \"Add README context extraction\", \"difficulty\": 2, \"description\": \"Add context from README\", \"timestamp\": \"2025-06-17T14:30:00Z\"}"
    
    # Create a mock response object with the content
    
    mock_response = mock.MagicMock()
    mock_response.choices = [MockChoice(mock_response_text)]
    
    # Mock the chat creation function
    with mock.patch("backlog_cli.openai_client._chat_create", return_value=mock_response):
        # Mock the system message loading
        with mock.patch("backlog_cli.openai_client._load_system_message"):
            # Mock the schema validation to pass
            with mock.patch("backlog_cli.openai_client._validate_schema", return_value=None):
                # Call the function
                result = call_openai("Add context extraction from README")
                
                # Check that JSON was correctly extracted
                assert result["title"] == "Add README context extraction"
                assert result["difficulty"] == 2


def test_json_extraction_with_text_after():
    """Test that JSON is correctly extracted from responses with text after the JSON."""
    from backlog_cli.openai_client import call_openai
    
    # Mock the OpenAI response to include text after the JSON
    mock_response_text = "{\"title\": \"Add README context extraction\", \"difficulty\": 2, \"description\": \"Add context from README\", \"timestamp\": \"2025-06-17T14:30:00Z\"}\n\nI hope this helps with your task!"
    
    mock_response = mock.MagicMock()
    mock_response.choices = [MockChoice(mock_response_text)]
    
    with mock.patch("backlog_cli.openai_client._chat_create", return_value=mock_response):
        with mock.patch("backlog_cli.openai_client._load_system_message"):
            with mock.patch("backlog_cli.openai_client._validate_schema", return_value=None):
                result = call_openai("Add context extraction from README")
                
                assert result["title"] == "Add README context extraction"
                assert result["difficulty"] == 2


def test_retry_on_json_error():
    """Test that the function retries on JSON parsing errors."""
    from backlog_cli.openai_client import call_openai
    import json
    
    # First response has invalid JSON, second response has valid JSON
    invalid_response = mock.MagicMock()
    invalid_response.choices = [MockChoice("Not a valid JSON response")]
    
    valid_response_text = "{\"title\": \"Retry Success\", \"difficulty\": 3, \"description\": \"Test retry logic\", \"timestamp\": \"2025-06-17T15:00:00Z\"}"
    valid_response = mock.MagicMock()
    valid_response.choices = [MockChoice(valid_response_text)]
    
    # Mock _chat_create to return invalid response first, then valid response
    chat_create_mock = mock.MagicMock(side_effect=[invalid_response, valid_response])
    
    with mock.patch("backlog_cli.openai_client._chat_create", chat_create_mock):
        with mock.patch("backlog_cli.openai_client._load_system_message"):
            with mock.patch("backlog_cli.openai_client._validate_schema", return_value=None):
                # This should succeed on the second attempt
                result = call_openai("Test retry logic")
                
                # Verify chat_create was called twice
                assert chat_create_mock.call_count == 2
                assert result["title"] == "Retry Success"
                assert result["difficulty"] == 3


def test_sanitize_dictation():
    """Test that dictation is properly sanitized."""
    from backlog_cli.openai_client import sanitize_dictation
    
    # Test basic whitespace normalization
    assert sanitize_dictation("  test   input  ") == "test input"
    
    # Test meta-instruction detection and prefixing
    assert sanitize_dictation("be more clever with the readme") == "Backlog item: be more clever with the readme"
    assert sanitize_dictation("make it work better") == "Backlog item: make it work better"
    
    # Test normal input (not a meta-instruction)
    assert sanitize_dictation("Add login functionality") == "Add login functionality"
