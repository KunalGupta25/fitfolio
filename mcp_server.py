import sys
from mcp_tools.tools import mcp
from core.config import settings

if __name__ == "__main__":
    print(f"Starting fitFolio FastMCP server on {settings.mcp_host}:{settings.mcp_port}/mcp ...")
    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        path="/mcp",
    )
