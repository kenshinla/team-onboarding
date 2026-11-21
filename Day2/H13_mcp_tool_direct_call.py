import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters


SERVER_FILE = Path(__file__).resolve().parent / "H11_mcp_server_v1.py"


async def main() -> None:
    parameters = StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE)])
    async with Client(parameters) as client:
        tools = await client.list_tools()
        print("MCP Tool 목록:", [tool.name for tool in tools.tools])
        result = await client.call_tool("get_customer_profile", {"customer_id": "C001"})
        data = result.structured_content
        if data is None:
            data = [block.text for block in result.content if hasattr(block, "text")]
        
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())