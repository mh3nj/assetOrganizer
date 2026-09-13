"""
affinity package — new unified Affinity (Canva-era) integration.
"""

from affinity.mcp_client import MCPClient, MCPError
from affinity.affinity import AffinityController

__all__ = ["MCPClient", "MCPError", "AffinityController"]
