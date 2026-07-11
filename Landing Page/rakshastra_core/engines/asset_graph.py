"""Backward-compatibility shim — canonical module is infrastructure_graph.py."""
from rakshastra_core.engines.infrastructure_graph import InfrastructureGraph, InfrastructureGraph as AssetGraph

__all__ = ["InfrastructureGraph", "AssetGraph"]
