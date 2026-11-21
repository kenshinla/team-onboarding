from mcp.server.mcpserver import MCPServer

mcp = MCPServer("hol-l02-day2-business-server")


@mcp.tool()
def get_customer_profile(customer_id: str) -> dict:
    """고객 ID로 교육용 상품 정보를 조회한다."""

    customers = {
        "C001": {"customer_id": "C001", "product": "인터넷 500M", "status": "정상"},
        "C002": {"customer_id": "C002", "product": "인터넷 1G", "status": "정상"},
    }
    return customers.get(customer_id.strip().upper(), {"error": "고객을 찾을 수 없습니다."})


@mcp.tool()
def get_incident_status(region: str) -> dict:
    """지역명으로 교육용 장애 정보를 조회한다."""

    incidents = {
        "서울": {"region": "서울", "status": "정상"},
        "부산": {"region": "부산", "status": "점검"},
    }
    return incidents.get(region.strip(), {"error": "지역을 찾을 수 없습니다."})


if __name__ == "__main__":
    # VS Code MCP 등록 또는 MCP Inspector에서 이 파일을 실행한다.
    mcp.run()