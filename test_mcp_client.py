#!/usr/bin/env python3
"""
MCP 서버 테스트 클라이언트
"""

import asyncio
import json
import requests

async def test_mcp_server():
    """MCP 서버의 모든 도구들을 테스트합니다."""
    
    base_url = "http://localhost:8080"
    
    # 서버 상태 확인
    try:
        response = requests.get(f"{base_url}/health")
        print("🔗 MCP 서버가 실행 중입니다!")
    except:
        print("❌ MCP 서버가 실행되지 않았습니다. 먼저 서버를 시작해주세요.")
        print("명령어: mcp run api_docs_mcp_server:server --host 0.0.0.0 --port 8080")
        return
    
    # 테스트할 도구들
    tools = [
        {
            "name": "analyze_api_docs",
            "params": {"url": "https://petstore.swagger.io/v2/swagger.json"},
            "description": "API 문서 분석"
        },
        {
            "name": "get_api_endpoints", 
            "params": {"url": "https://petstore.swagger.io/v2/swagger.json"},
            "description": "API 엔드포인트 목록 조회"
        },
        {
            "name": "get_api_info",
            "params": {"url": "https://petstore.swagger.io/v2/swagger.json"},
            "description": "API 정보 조회"
        },
        {
            "name": "search_endpoints",
            "params": {"url": "https://petstore.swagger.io/v2/swagger.json", "search_term": "pet"},
            "description": "엔드포인트 검색"
        },
        {
            "name": "generate_code_examples",
            "params": {"url": "https://petstore.swagger.io/v2/swagger.json", "endpoint_path": "/pet/{petId}"},
            "description": "코드 예시 생성"
        },
        {
            "name": "health_check_api",
            "params": {"url": "https://petstore.swagger.io/v2/swagger.json", "max_endpoints": 3},
            "description": "API 상태 확인"
        },
        {
            "name": "export_api_docs",
            "params": {"url": "https://petstore.swagger.io/v2/swagger.json", "format": "json"},
            "description": "문서 내보내기"
        }
    ]
    
    for i, tool in enumerate(tools, 1):
        print(f"\n📊 {i}. {tool['description']} 테스트")
        try:
            # MCP 서버에 직접 HTTP 요청
            response = requests.post(
                f"{base_url}/tools/{tool['name']}",
                json=tool['params'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {tool['description']} 성공!")
                content = str(result.get('content', result))
                print(content[:300] + "..." if len(content) > 300 else content)
            else:
                print(f"❌ {tool['description']} 실패: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ {tool['description']} 실패: {e}")

if __name__ == "__main__":
    print("🚀 MCP 서버 테스트 시작...")
    asyncio.run(test_mcp_server())
    print("\n✅ 모든 테스트 완료!") 