"""Digital Twin Plugin for Rakshastra Core.

Provides graph-based simulation of red-team cyber attacks and defensive what-if interventions.
"""

from typing import Any, Dict

from plugins.plugin_utils import make_lazy_engine

get_digital_twin_engine = make_lazy_engine(
    "rakshastra_core.engines.digital_twin_engine",
    "DigitalTwinEngine",
    "digital_twin.db",
)


def on_post_tool_call(tool_name: str, result: Dict[str, Any], **kwargs) -> None:
    """Optional post-tool-call inspection hook for Digital Twin plugin."""
    pass
