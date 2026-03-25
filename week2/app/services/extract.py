from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from dotenv import load_dotenv
import ollama

load_dotenv()

ollama_url = os.getenv("OLLAMA_BASE_URL")
client = ollama.Client(host=ollama_url)

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def extract_action_items_llm(text: str) -> List[str]:
    """
    Extract action items from text using an LLM (Ollama + Mistral).

    This function uses a large language model to intelligently extract action items
    from free-form notes, providing more semantic understanding than regex-based heuristics.
    It requests structured JSON output to ensure reliable parsing.

    Args:
        text: The input text containing notes or action items.

    Returns:
        A list of extracted action items as strings. Returns an empty list if:
        - The input text is empty
        - The Ollama service is unavailable
        - The LLM fails to generate a valid response

    Example:
        >>> items = extract_action_items_llm("- Fix the login bug\nTodo: Write unit tests")
        >>> print(items)
        ['Fix the login bug', 'Write unit tests']
    """
    # Return early if input is empty
    if not text or not text.strip():
        return []

    try:
        # Define JSON schema for structured output
        # Instructs Ollama to return a JSON object with 'action_items' array
        schema = {
            "type": "object",
            "properties": {
                "action_items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of extracted action items"
                }
            },
            "required": ["action_items"]
        }

        # Create messages for the LLM
        system_prompt = (
            "You are an expert action item extractor. Your task is to identify and extract "
            "all actionable items, tasks, and to-dos from the provided notes. "
            "Return ONLY the JSON object with the 'action_items' array, no other text. "
            "Each action item should be a clear, concise statement of what needs to be done."
        )

        user_prompt = f"Extract all action items from these notes:\n\n{text}"

        # Call Ollama with structured output
        response = client.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            format=schema,
            stream=False
        )

        # Parse the response
        response_text = response.get("message", {}).get("content", "")
        if not response_text:
            return []

        # Parse JSON from response
        response_json = json.loads(response_text)
        action_items = response_json.get("action_items", [])

        # Ensure we return a list of strings, filter out empty items
        cleaned_items = [item.strip() for item in action_items if isinstance(item, str) and item.strip()]

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for item in cleaned_items:
            lowered = item.lower()
            if lowered not in seen:
                seen.add(lowered)
                unique.append(item)

        return unique

    except json.JSONDecodeError:
        # Log the error but return empty list gracefully
        print("Warning: Failed to parse LLM response as JSON")
        return []
    except Exception as e:
        # Handle any Ollama connection errors or other exceptions
        # Return empty list instead of crashing
        print(f"Warning: LLM extraction failed: {e}")
        return []
