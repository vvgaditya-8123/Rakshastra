"""Tests for the Rakshastra-3/4 non-agentic warning detector.

Prior to this check, the warning fired on any model whose name contained
``"rakshastra"`` anywhere (case-insensitive). That false-positived on unrelated
local Modelfiles such as ``rakshastra-brain:qwen3-14b-ctx16k`` — a tool-capable
Qwen3 wrapper that happens to live under the "rakshastra" tag namespace.

``is_nous_rakshastra_non_agentic`` should only match the actual
Rakshastra-3 / Rakshastra-4 chat family.
"""

from __future__ import annotations

import pytest

from rakshastra_cli.model_switch import (
    _RAKSHASTRA_MODEL_WARNING,
    _check_rakshastra_model_warning,
    is_nous_rakshastra_non_agentic,
)


@pytest.mark.parametrize(
    "model_name",
    [
        "NousResearch/Rakshastra-3-Llama-3.1-70B",
        "NousResearch/Rakshastra-3-Llama-3.1-405B",
        "rakshastra-3",
        "Rakshastra-3",
        "rakshastra-4",
        "rakshastra-4-405b",
        "rakshastra_4_70b",
        "openrouter/rakshastra3:70b",
        "openrouter/nousresearch/rakshastra-4-405b",
        "NousResearch/Rakshastra3",
        "rakshastra-3.1",
    ],
)
def test_matches_real_nous_rakshastra_chat_models(model_name: str) -> None:
    assert is_nous_rakshastra_non_agentic(model_name), (
        f"expected {model_name!r} to be flagged as Rakshastra 3/4"
    )
    assert _check_rakshastra_model_warning(model_name) == _RAKSHASTRA_MODEL_WARNING


@pytest.mark.parametrize(
    "model_name",
    [
        # Kyle's local Modelfile — qwen3:14b under a custom tag
        "rakshastra-brain:qwen3-14b-ctx16k",
        "rakshastra-brain:qwen3-14b-ctx32k",
        "rakshastra-honcho:qwen3-8b-ctx8k",
        # Plain unrelated models
        "qwen3:14b",
        "qwen3-coder:30b",
        "qwen2.5:14b",
        "claude-opus-4-6",
        "anthropic/claude-sonnet-4.5",
        "gpt-5",
        "openai/gpt-4o",
        "google/gemini-2.5-flash",
        "deepseek-chat",
        # Non-chat Rakshastra models we don't warn about
        "rakshastra-llm-2",
        "rakshastra2-pro",
        "nous-rakshastra-2-mistral",
        # Edge cases
        "",
        "rakshastra",  # bare "rakshastra" isn't the 3/4 family
        "rakshastra-brain",
        "brain-rakshastra-3-impostor",  # "3" not preceded by /: boundary
    ],
)
def test_does_not_match_unrelated_models(model_name: str) -> None:
    assert not is_nous_rakshastra_non_agentic(model_name), (
        f"expected {model_name!r} NOT to be flagged as Rakshastra 3/4"
    )
    assert _check_rakshastra_model_warning(model_name) == ""


def test_none_like_inputs_are_safe() -> None:
    assert is_nous_rakshastra_non_agentic("") is False
    # Defensive: the helper shouldn't crash on None-ish falsy input either.
    assert _check_rakshastra_model_warning("") == ""
