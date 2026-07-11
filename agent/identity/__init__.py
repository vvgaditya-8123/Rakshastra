"""Modular identity and guidance configurations for the Rakshastra Agent runtime prompt."""

from agent.identity.identity import DEFAULT_AGENT_IDENTITY, RAKSHASTRA_AGENT_HELP_GUIDANCE
from agent.identity.memory_guidance import MEMORY_GUIDANCE
from agent.identity.security_guidance import SECURITY_GUIDANCE, SECURITY_REASONING_GUIDANCE
from agent.identity.tool_guidance import TOOL_GUIDANCE
from agent.identity.reporting_guidance import REPORTING_GUIDANCE

__all__ = [
    "DEFAULT_AGENT_IDENTITY",
    "RAKSHASTRA_AGENT_HELP_GUIDANCE",
    "MEMORY_GUIDANCE",
    "SECURITY_GUIDANCE",
    "SECURITY_REASONING_GUIDANCE",
    "TOOL_GUIDANCE",
    "REPORTING_GUIDANCE",
]
