#!/usr/bin/env python3
"""
API Docs MCP Server (FastMCP Version)

이 서버는 특정 서버의 API 문서를 분석하여 프론트엔드에서 사용할 수 있는 API를 추천해주는 MCP 서버입니다.
FastMCP 규격에 맞게 리팩토링되었습니다.
"""

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP, tool
from pydantic import Field, BaseModel


# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO)
# urllib3의 InsecureRequestWarning 로그 비활성화
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


# --- Pydantic 모델 정의 ---
class APIEndpoint(BaseModel):
    path: str
    method: str
    summary: str = ""
    description: str = ""
    tags: List[str] = []

class FrontendRecommendation(BaseModel):
    page: str
    description: str
    endpoints: List[APIEndpoint]

class AnalysisResult(BaseModel):
    title: str
    version: str
    description: str
    endpoints: List[APIEndpoint]
    recommendations: List[FrontendRecommendation]


# --- API 분석기 클래스 ---
class APIDocsAnalyzer:
    """API 문서를 분석하는 클래스"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_swagger_docs(self, base_url: str, cookies: Optional[Dict[str, str]] = None) -> Optional[Dict]:
        """Swagger/OpenAPI 문서를 가져옵니다"""
        common_paths = ['/swagger.json', '/api-docs', '/openapi.json', '/v2/api-docs', '/v3/api-docs']
        for path in common_paths:
            try:
                url = urljoin(base_url, path)
                response = self.session.get(url, timeout=10, cookies=cookies, verify=False)
                if response.status_code == 200:
                    logger.info(f"성공적으로 Swagger 문서를 {url} 에서 찾았습니다.")
                    return response.json()
            except requests.RequestException as e:
                logger.debug(f"Swagger 문서 가져오기 실패 {url}: {e}")
        return None

    def fetch_html_docs(self, url: str, cookies: Optional[Dict[str, str]] = None) -> Optional[str]:
        """HTML 형태의 API 문서를 가져옵니다"""
        try:
            response = self.session.get(url, timeout=10, cookies=cookies, verify=False)
            if response.status_code == 200:
                logger.info(f"성공적으로 HTML 문서를 {url} 에서 가져왔습니다.")
                return response.text
        except requests.RequestException as e:
            logger.error(f"HTML 문서 가져오기 실패: {e}")
        return None

    def analyze_swagger_docs(self, swagger_doc: Dict) -> AnalysisResult:
        """Swagger/OpenAPI 문서를 분석합니다"""
        endpoints = []
        paths = swagger_doc.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoints.append(APIEndpoint(
                        path=path,
                        method=method.upper(),
                        summary=details.get('summary', ''),
                        description=details.get('description', ''),
                        tags=details.get('tags', []),
                    ))
        
        recommendations = self._generate_frontend_recommendations(endpoints)
        
        return AnalysisResult(
            title=swagger_doc.get('info', {}).get('title', 'Unknown API'),
            version=swagger_doc.get('info', {}).get('version', 'Unknown'),
            description=swagger_doc.get('info', {}).get('description', ''),
            endpoints=endpoints,
            recommendations=recommendations,
        )
        
    def _generate_frontend_recommendations(self, endpoints: List[APIEndpoint]) -> List[FrontendRecommendation]:
        """프론트엔드 구현을 위한 API 추천을 생성합니다"""
        page_groups = {
            '사용자 관리': [], '인증/로그인': [], '데이터 조회': [],
            '데이터 생성/수정': [], '파일 업로드': [], '검색': [], '통계/분석': []
        }
        for endpoint in endpoints:
            path = endpoint.path.lower()
            summary = endpoint.summary.lower()
            if any(w in path or w in summary for w in ['user', 'member']):
                page_groups['사용자 관리'].append(endpoint)
            elif any(w in path or w in summary for w in ['auth', 'login']):
                page_groups['인증/로그인'].append(endpoint)
            elif endpoint.method == 'GET':
                page_groups['데이터 조회'].append(endpoint)
            elif endpoint.method in ['POST', 'PUT', 'PATCH']:
                page_groups['데이터 생성/수정'].append(endpoint)
            # ... 다른 규칙들 추가 가능

        return [
            FrontendRecommendation(
                page=page_name,
                description=f'{page_name} 기능 구현을 위한 API들',
                endpoints=page_endpoints
            ) for page_name, page_endpoints in page_groups.items() if page_endpoints
        ]


# --- MCP 서버 설정 ---
server = FastMCP(
    name="api-docs-analyzer",
    version="1.1.0",
    instructions="API 문서 URL과 인증 쿠키를 제공하면, 해당 API를 분석하여 프론트엔드 페이지 구현 방법을 추천해드립니다."
)
analyzer = APIDocsAnalyzer()


# --- MCP 도구 정의 ---
@tool(server)
def analyze_api_docs(
    url: str = Field(..., description="분석할 API 문서의 URL (Swagger/OpenAPI JSON 또는 HTML 페이지)"),
    cookies: Optional[Dict[str, str]] = Field(None, description="인증에 필요한 쿠키 (예: {'_oauth2_proxy': 'value'})")
) -> str:
    """
    주어진 URL의 API 문서를 분석하여, 프론트엔드에서 사용할 수 있는 페이지별 API 목록을 추천합니다.
    """
    logger.info(f"'{url}' 분석 시작. 쿠키 사용: {'예' if cookies else '아니오'}")
    
    # 1. Swagger/OpenAPI 문서 시도
    swagger_doc = analyzer.fetch_swagger_docs(url, cookies)
    if not swagger_doc:
        # 2. HTML 문서 시도 (Swagger UI 등)
        html_content = analyzer.fetch_html_docs(url, cookies)
        if html_content:
            # HTML에서 swagger.json 경로 찾기 시도
            match = re.search(r'url:\s*"([^"]+\.json)"', html_content)
            if match:
                swagger_url = urljoin(url, match.group(1))
                logger.info(f"HTML에서 Swagger URL 발견: {swagger_url}")
                swagger_doc = analyzer.fetch_swagger_docs(swagger_url, cookies)

    if not swagger_doc:
        return "❌ API 문서를 찾거나 분석할 수 없습니다. URL과 쿠키를 확인해주세요."

    try:
        analysis = analyzer.analyze_swagger_docs(swagger_doc)
        
        # 결과 텍스트 생성
        result_text = f"✅ **API 문서 분석 완료: {analysis.title} ({analysis.version})**\n\n"
        result_text += f"총 {len(analysis.endpoints)}개의 API 엔드포인트를 발견했습니다.\n\n"
        result_text += "--- 📄 프론트엔드 페이지 구현 추천 ---\n\n"

        if not analysis.recommendations:
            result_text += "추천할 만한 페이지 그룹을 찾지 못했습니다."
            return result_text
            
        for rec in analysis.recommendations:
            result_text += f"### 💡 {rec.page} 페이지\n"
            result_text += f"_{rec.description}_\n"
            for endpoint in rec.endpoints[:5]: # 너무 길지 않게 5개만 표시
                result_text += f"- `{endpoint.method}` {endpoint.path} ({endpoint.summary})\n"
            if len(rec.endpoints) > 5:
                result_text += f"- ... 외 {len(rec.endpoints) - 5}개\n"
            result_text += "\n"
            
        return result_text

    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}", exc_info=True)
        return f"❌ 분석 중 오류가 발생했습니다: {e}" 