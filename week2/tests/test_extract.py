import os
import pytest
import json
from unittest.mock import patch, MagicMock

from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# ============================================================================
# Unit Tests for extract_action_items_llm() - LLM-powered extraction
# ============================================================================

@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_with_bullets(mock_chat):
    """Test LLM extraction with bullet-point formatted action items."""
    # Mock the Ollama chat response
    mock_chat.return_value = {
        "message": {
            "content": json.dumps({
                "action_items": [
                    "Set up database",
                    "Implement API extract endpoint",
                    "Write tests"
                ]
            })
        }
    }

    text = """
    Notes from meeting:
    - [ ] Set up database
    * Implement API extract endpoint
    1. Write tests
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) == 3
    assert "Set up database" in items
    assert "Implement API extract endpoint" in items
    assert "Write tests" in items


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_with_keywords(mock_chat):
    """Test LLM extraction with keyword-prefixed action items (todo:, action:, next:)."""
    mock_chat.return_value = {
        "message": {
            "content": json.dumps({
                "action_items": [
                    "Update documentation",
                    "Fix authentication bug",
                    "Review pull request"
                ]
            })
        }
    }

    text = """
    Project notes:
    todo: Update documentation
    action: Fix authentication bug
    next: Review pull request
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) == 3
    assert "Update documentation" in items
    assert "Fix authentication bug" in items
    assert "Review pull request" in items


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_with_natural_language(mock_chat):
    """Test LLM extraction from natural language narrative text."""
    mock_chat.return_value = {
        "message": {
            "content": json.dumps({
                "action_items": [
                    "Refactor the authentication module",
                    "Add unit tests for payment processing",
                    "Document the API endpoints"
                ]
            })
        }
    }

    text = """
    In the next sprint, we need to refactor the authentication module to improve 
    performance. We should also add unit tests for payment processing to ensure 
    reliability. Finally, someone needs to document the API endpoints.
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) == 3
    assert any("refactor" in item.lower() for item in items)
    assert any("unit test" in item.lower() for item in items)
    assert any("document" in item.lower() for item in items)


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_empty_input(mock_chat):
    """Test LLM extraction with empty input returns empty list."""
    # Should not even call the API for empty input
    items = extract_action_items_llm("")
    assert items == []
    mock_chat.assert_not_called()

    # Also test whitespace-only input
    items = extract_action_items_llm("   \n  \t  ")
    assert items == []
    mock_chat.assert_not_called()


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_mixed_formats(mock_chat):
    """Test LLM extraction with mixed format input (bullets + keywords + narrative)."""
    mock_chat.return_value = {
        "message": {
            "content": json.dumps({
                "action_items": [
                    "Set up CI/CD pipeline",
                    "Write integration tests",
                    "Deploy to staging environment",
                    "Gather user feedback"
                ]
            })
        }
    }

    text = """
    Sprint planning notes:
    - [ ] Set up CI/CD pipeline
    todo: Write integration tests
    
    We should deploy to staging environment and gather user feedback.
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) == 4
    assert "Set up CI/CD pipeline" in items
    assert "Write integration tests" in items
    assert "Deploy to staging environment" in items
    assert "Gather user feedback" in items


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_deduplication(mock_chat):
    """Test that LLM extraction removes duplicates while preserving order."""
    mock_chat.return_value = {
        "message": {
            "content": json.dumps({
                "action_items": [
                    "Fix bug in login",
                    "Fix bug in login",  # Duplicate
                    "Update API documentation"
                ]
            })
        }
    }

    text = "Fix the login bug and update API documentation."
    items = extract_action_items_llm(text)

    # Should deduplicate but preserve order
    assert len(items) == 2
    assert items[0].lower() == "fix bug in login"
    assert items[1].lower() == "update api documentation"


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_invalid_json(mock_chat):
    """Test graceful handling when LLM returns invalid JSON."""
    mock_chat.return_value = {
        "message": {
            "content": "This is not valid JSON"
        }
    }

    text = "Fix the bug and write tests"
    items = extract_action_items_llm(text)

    # Should return empty list instead of crashing
    assert items == []


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_connection_error(mock_chat):
    """Test graceful handling when Ollama service is unavailable."""
    mock_chat.side_effect = Exception("Connection refused: Ollama service not running")

    text = "Fix the bug and write tests"
    items = extract_action_items_llm(text)

    # Should return empty list instead of crashing
    assert items == []


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_empty_items_array(mock_chat):
    """Test handling of empty action items array from LLM."""
    mock_chat.return_value = {
        "message": {
            "content": json.dumps({
                "action_items": []
            })
        }
    }

    text = "Some narrative text without clear action items"
    items = extract_action_items_llm(text)

    assert items == []


@patch("week2.app.services.extract.client.chat")
def test_extract_action_items_llm_strips_whitespace(mock_chat):
    """Test that extracted items are stripped of extra whitespace."""
    mock_chat.return_value = {
        "message": {
            "content": json.dumps({
                "action_items": [
                    "  Fix the login bug  ",
                    "\nWrite documentation\n",
                    "Update tests"
                ]
            })
        }
    }

    text = "Fix login. Write docs. Update tests."
    items = extract_action_items_llm(text)

    assert len(items) == 3
    assert items[0] == "Fix the login bug"
    assert items[1] == "Write documentation"
    assert items[2] == "Update tests"
    # Ensure no leading/trailing whitespace
    for item in items:
        assert item == item.strip()
