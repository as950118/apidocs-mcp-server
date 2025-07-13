#!/usr/bin/env python3
"""
API Docs MCP Server (FastMCP Version)

이 서버는 특정 서버의 API 문서를 분석하여 프론트엔드에서 사용할 수 있는 API를 추천해주는 MCP 서버입니다.
FastMCP 규격에 맞게 리팩토링되었습니다.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime

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
    parameters: List[Dict[str, Any]] = []
    responses: Dict[str, Any] = {}

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
    base_url: str = ""
    total_endpoints: int = 0

class APIHealthCheck(BaseModel):
    endpoint: str
    method: str
    status: str
    response_time: float
    error_message: Optional[str] = None

class CodeExample(BaseModel):
    language: str
    code: str
    description: str


# --- API 분석기 클래스 ---
class APIDocsAnalyzer:
    """API 문서를 분석하는 클래스"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}

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

    def analyze_swagger_docs(self, swagger_doc: Dict, base_url: str = "") -> AnalysisResult:
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
                        parameters=details.get('parameters', []),
                        responses=details.get('responses', {}),
                    ))
        
        recommendations = self._generate_frontend_recommendations(endpoints)
        
        return AnalysisResult(
            title=swagger_doc.get('info', {}).get('title', 'Unknown API'),
            version=swagger_doc.get('info', {}).get('version', 'Unknown'),
            description=swagger_doc.get('info', {}).get('description', ''),
            endpoints=endpoints,
            recommendations=recommendations,
            base_url=base_url,
            total_endpoints=len(endpoints),
        )
        
    def _generate_frontend_recommendations(self, endpoints: List[APIEndpoint]) -> List[FrontendRecommendation]:
        """프론트엔드 구현을 위한 API 추천을 생성합니다"""
        page_groups = {
            '사용자 관리': [], '인증/로그인': [], '데이터 조회': [],
            '데이터 생성/수정': [], '파일 업로드': [], '검색': [], '통계/분석': [],
            '결제/결제': [], '알림/메시지': [], '설정/관리': []
        }
        
        for endpoint in endpoints:
            path = endpoint.path.lower()
            summary = endpoint.summary.lower()
            tags = [tag.lower() for tag in endpoint.tags]
            
            # 사용자 관리
            if any(w in path or w in summary or w in tags for w in ['user', 'member', 'customer']):
                page_groups['사용자 관리'].append(endpoint)
            # 인증/로그인
            elif any(w in path or w in summary or w in tags for w in ['auth', 'login', 'token', 'oauth']):
                page_groups['인증/로그인'].append(endpoint)
            # 결제/결제
            elif any(w in path or w in summary or w in tags for w in ['payment', 'pay', 'billing', 'charge']):
                page_groups['결제/결제'].append(endpoint)
            # 파일 업로드
            elif any(w in path or w in summary or w in tags for w in ['upload', 'file', 'image', 'media']):
                page_groups['파일 업로드'].append(endpoint)
            # 검색
            elif any(w in path or w in summary or w in tags for w in ['search', 'find', 'query']):
                page_groups['검색'].append(endpoint)
            # 통계/분석
            elif any(w in path or w in summary or w in tags for w in ['stats', 'analytics', 'report', 'metric']):
                page_groups['통계/분석'].append(endpoint)
            # 알림/메시지
            elif any(w in path or w in summary or w in tags for w in ['notification', 'message', 'alert', 'push']):
                page_groups['알림/메시지'].append(endpoint)
            # 설정/관리
            elif any(w in path or w in summary or w in tags for w in ['config', 'setting', 'admin', 'management']):
                page_groups['설정/관리'].append(endpoint)
            # 데이터 조회
            elif endpoint.method == 'GET':
                page_groups['데이터 조회'].append(endpoint)
            # 데이터 생성/수정
            elif endpoint.method in ['POST', 'PUT', 'PATCH']:
                page_groups['데이터 생성/수정'].append(endpoint)

        return [
            FrontendRecommendation(
                page=page_name,
                description=f'{page_name} 기능 구현을 위한 API들',
                endpoints=page_endpoints
            ) for page_name, page_endpoints in page_groups.items() if page_endpoints
        ]

    def health_check_endpoint(self, base_url: str, endpoint: APIEndpoint, timeout: int = 5) -> APIHealthCheck:
        """개별 엔드포인트의 상태를 확인합니다"""
        try:
            url = urljoin(base_url, endpoint.path)
            start_time = datetime.now()
            
            if endpoint.method == 'GET':
                response = self.session.get(url, timeout=timeout, verify=False)
            elif endpoint.method == 'POST':
                response = self.session.post(url, json={}, timeout=timeout, verify=False)
            else:
                # GET으로 테스트 (실제 요청은 하지 않음)
                response = self.session.get(url, timeout=timeout, verify=False)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code < 400:
                status = "✅ 정상"
            elif response.status_code == 401:
                status = "🔐 인증 필요"
            elif response.status_code == 403:
                status = "🚫 권한 없음"
            elif response.status_code == 404:
                status = "❌ 찾을 수 없음"
            else:
                status = f"⚠️ 오류 ({response.status_code})"
                
            return APIHealthCheck(
                endpoint=endpoint.path,
                method=endpoint.method,
                status=status,
                response_time=response_time
            )
            
        except requests.RequestException as e:
            return APIHealthCheck(
                endpoint=endpoint.path,
                method=endpoint.method,
                status="❌ 연결 실패",
                response_time=0,
                error_message=str(e)
            )

    def generate_code_examples(self, endpoint: APIEndpoint, base_url: str) -> List[CodeExample]:
        """API 엔드포인트에 대한 코드 예시를 생성합니다"""
        examples = []
        
        # JavaScript/TypeScript 예시
        js_code = f"""// {endpoint.summary}
const response = await fetch('{urljoin(base_url, endpoint.path)}', {{
  method: '{endpoint.method}',
  headers: {{
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  }}{',\n  body: JSON.stringify({\n    // 요청 데이터\n  })' if endpoint.method in ['POST', 'PUT', 'PATCH'] else ''}
}});

const data = await response.json();
console.log(data);"""
        
        examples.append(CodeExample(
            language="JavaScript/TypeScript",
            code=js_code,
            description=f"{endpoint.method} {endpoint.path} API 호출 예시"
        ))
        
        # Python 예시
        python_code = f"""# {endpoint.summary}
import requests

url = '{urljoin(base_url, endpoint.path)}'
headers = {{
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
}}{f'''

data = {{
    # 요청 데이터
}}

response = requests.{endpoint.method.lower()}(url, json=data, headers=headers)''' if endpoint.method in ['POST', 'PUT', 'PATCH'] else f'''

response = requests.{endpoint.method.lower()}(url, headers=headers)'}

print(response.json())"""
        
        examples.append(CodeExample(
            language="Python",
            code=python_code,
            description=f"{endpoint.method} {endpoint.path} API 호출 예시"
        ))
        
        return examples


# --- MCP 서버 설정 ---
server = FastMCP(
    name="api-docs-analyzer",
    version="2.0.0",
    instructions="API 문서 URL과 인증 쿠키를 제공하면, 해당 API를 분석하여 프론트엔드 페이지 구현 방법을 추천해드립니다. 다양한 도구를 통해 API 문서를 분석하고, 코드 예시를 생성하며, API 상태를 확인할 수 있습니다."
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
        analysis = analyzer.analyze_swagger_docs(swagger_doc, url)
        
        # 결과 텍스트 생성
        result_text = f"✅ **API 문서 분석 완료: {analysis.title} ({analysis.version})**\n\n"
        result_text += f"총 {analysis.total_endpoints}개의 API 엔드포인트를 발견했습니다.\n\n"
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


@tool(server)
def get_api_endpoints(
    url: str = Field(..., description="분석할 API 문서의 URL"),
    cookies: Optional[Dict[str, str]] = Field(None, description="인증에 필요한 쿠키")
) -> str:
    """
    API 문서에서 모든 엔드포인트 목록을 가져옵니다.
    """
    logger.info(f"'{url}' 엔드포인트 목록 조회 시작")
    
    swagger_doc = analyzer.fetch_swagger_docs(url, cookies)
    if not swagger_doc:
        return "❌ API 문서를 찾을 수 없습니다."
    
    try:
        analysis = analyzer.analyze_swagger_docs(swagger_doc, url)
        
        result_text = f"📋 **API 엔드포인트 목록: {analysis.title}**\n\n"
        result_text += f"총 {analysis.total_endpoints}개의 엔드포인트\n\n"
        
        # 태그별로 그룹화
        tag_groups = {}
        for endpoint in analysis.endpoints:
            for tag in endpoint.tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(endpoint)
        
        for tag, endpoints in tag_groups.items():
            result_text += f"### 🏷️ {tag}\n"
            for endpoint in endpoints:
                result_text += f"- `{endpoint.method}` {endpoint.path}\n"
                if endpoint.summary:
                    result_text += f"  - {endpoint.summary}\n"
            result_text += "\n"
        
        return result_text
        
    except Exception as e:
        logger.error(f"엔드포인트 목록 조회 중 오류: {e}")
        return f"❌ 엔드포인트 목록 조회 중 오류가 발생했습니다: {e}"


@tool(server)
def health_check_api(
    url: str = Field(..., description="API 문서의 URL"),
    cookies: Optional[Dict[str, str]] = Field(None, description="인증에 필요한 쿠키"),
    max_endpoints: int = Field(10, description="테스트할 최대 엔드포인트 수")
) -> str:
    """
    API 엔드포인트들의 상태를 확인합니다.
    """
    logger.info(f"'{url}' API 상태 확인 시작")
    
    swagger_doc = analyzer.fetch_swagger_docs(url, cookies)
    if not swagger_doc:
        return "❌ API 문서를 찾을 수 없습니다."
    
    try:
        analysis = analyzer.analyze_swagger_docs(swagger_doc, url)
        
        # GET 엔드포인트만 테스트 (안전한 요청)
        get_endpoints = [ep for ep in analysis.endpoints if ep.method == 'GET'][:max_endpoints]
        
        result_text = f"🔍 **API 상태 확인: {analysis.title}**\n\n"
        result_text += f"테스트할 엔드포인트: {len(get_endpoints)}개\n\n"
        
        for endpoint in get_endpoints:
            health = analyzer.health_check_endpoint(url, endpoint)
            result_text += f"### {endpoint.method} {endpoint.path}\n"
            result_text += f"- 상태: {health.status}\n"
            if health.response_time > 0:
                result_text += f"- 응답 시간: {health.response_time:.2f}초\n"
            if health.error_message:
                result_text += f"- 오류: {health.error_message}\n"
            result_text += "\n"
        
        return result_text
        
    except Exception as e:
        logger.error(f"API 상태 확인 중 오류: {e}")
        return f"❌ API 상태 확인 중 오류가 발생했습니다: {e}"


@tool(server)
def generate_code_examples(
    url: str = Field(..., description="API 문서의 URL"),
    endpoint_path: str = Field(..., description="코드 예시를 생성할 엔드포인트 경로"),
    cookies: Optional[Dict[str, str]] = Field(None, description="인증에 필요한 쿠키")
) -> str:
    """
    특정 API 엔드포인트에 대한 코드 예시를 생성합니다.
    """
    logger.info(f"'{endpoint_path}' 코드 예시 생성 시작")
    
    swagger_doc = analyzer.fetch_swagger_docs(url, cookies)
    if not swagger_doc:
        return "❌ API 문서를 찾을 수 없습니다."
    
    try:
        analysis = analyzer.analyze_swagger_docs(swagger_doc, url)
        
        # 엔드포인트 찾기
        target_endpoint = None
        for endpoint in analysis.endpoints:
            if endpoint.path == endpoint_path:
                target_endpoint = endpoint
                break
        
        if not target_endpoint:
            return f"❌ 엔드포인트 '{endpoint_path}'를 찾을 수 없습니다."
        
        examples = analyzer.generate_code_examples(target_endpoint, url)
        
        result_text = f"💻 **코드 예시: {target_endpoint.method} {target_endpoint.path}**\n\n"
        result_text += f"**설명**: {target_endpoint.summary}\n\n"
        
        for example in examples:
            result_text += f"### {example.language}\n"
            result_text += f"```{example.language.lower().split('/')[0]}\n{example.code}\n```\n\n"
        
        return result_text
        
    except Exception as e:
        logger.error(f"코드 예시 생성 중 오류: {e}")
        return f"❌ 코드 예시 생성 중 오류가 발생했습니다: {e}"


@tool(server)
def search_endpoints(
    url: str = Field(..., description="API 문서의 URL"),
    search_term: str = Field(..., description="검색할 키워드"),
    cookies: Optional[Dict[str, str]] = Field(None, description="인증에 필요한 쿠키")
) -> str:
    """
    API 엔드포인트에서 특정 키워드를 검색합니다.
    """
    logger.info(f"'{search_term}' 키워드로 엔드포인트 검색 시작")
    
    swagger_doc = analyzer.fetch_swagger_docs(url, cookies)
    if not swagger_doc:
        return "❌ API 문서를 찾을 수 없습니다."
    
    try:
        analysis = analyzer.analyze_swagger_docs(swagger_doc, url)
        
        search_term_lower = search_term.lower()
        matched_endpoints = []
        
        for endpoint in analysis.endpoints:
            if (search_term_lower in endpoint.path.lower() or 
                search_term_lower in endpoint.summary.lower() or
                search_term_lower in endpoint.description.lower() or
                any(search_term_lower in tag.lower() for tag in endpoint.tags)):
                matched_endpoints.append(endpoint)
        
        result_text = f"🔍 **검색 결과: '{search_term}'**\n\n"
        result_text += f"총 {len(matched_endpoints)}개의 엔드포인트를 찾았습니다.\n\n"
        
        for endpoint in matched_endpoints:
            result_text += f"### {endpoint.method} {endpoint.path}\n"
            result_text += f"- **설명**: {endpoint.summary}\n"
            if endpoint.tags:
                result_text += f"- **태그**: {', '.join(endpoint.tags)}\n"
            result_text += "\n"
        
        if not matched_endpoints:
            result_text += "검색 결과가 없습니다."
        
        return result_text
        
    except Exception as e:
        logger.error(f"엔드포인트 검색 중 오류: {e}")
        return f"❌ 엔드포인트 검색 중 오류가 발생했습니다: {e}"


@tool(server)
def get_api_info(
    url: str = Field(..., description="API 문서의 URL"),
    cookies: Optional[Dict[str, str]] = Field(None, description="인증에 필요한 쿠키")
) -> str:
    """
    API 문서의 기본 정보를 가져옵니다.
    """
    logger.info(f"'{url}' API 정보 조회 시작")
    
    swagger_doc = analyzer.fetch_swagger_docs(url, cookies)
    if not swagger_doc:
        return "❌ API 문서를 찾을 수 없습니다."
    
    try:
        analysis = analyzer.analyze_swagger_docs(swagger_doc, url)
        
        result_text = f"📊 **API 정보: {analysis.title}**\n\n"
        result_text += f"- **버전**: {analysis.version}\n"
        result_text += f"- **총 엔드포인트**: {analysis.total_endpoints}개\n"
        result_text += f"- **기본 URL**: {analysis.base_url}\n\n"
        
        if analysis.description:
            result_text += f"**설명**:\n{analysis.description}\n\n"
        
        # 메서드별 통계
        method_stats = {}
        for endpoint in analysis.endpoints:
            method = endpoint.method
            method_stats[method] = method_stats.get(method, 0) + 1
        
        result_text += "**메서드별 통계**:\n"
        for method, count in sorted(method_stats.items()):
            result_text += f"- {method}: {count}개\n"
        
        result_text += "\n"
        
        # 태그별 통계
        tag_stats = {}
        for endpoint in analysis.endpoints:
            for tag in endpoint.tags:
                tag_stats[tag] = tag_stats.get(tag, 0) + 1
        
        if tag_stats:
            result_text += "**태그별 통계**:\n"
            for tag, count in sorted(tag_stats.items(), key=lambda x: x[1], reverse=True):
                result_text += f"- {tag}: {count}개\n"
        
        return result_text
        
    except Exception as e:
        logger.error(f"API 정보 조회 중 오류: {e}")
        return f"❌ API 정보 조회 중 오류가 발생했습니다: {e}"


@tool(server)
def export_api_docs(
    url: str = Field(..., description="API 문서의 URL"),
    format: str = Field("json", description="내보낼 형식 (json, markdown)"),
    cookies: Optional[Dict[str, str]] = Field(None, description="인증에 필요한 쿠키")
) -> str:
    """
    API 문서를 다양한 형식으로 내보냅니다.
    """
    logger.info(f"'{url}' API 문서 내보내기 시작 (형식: {format})")
    
    swagger_doc = analyzer.fetch_swagger_docs(url, cookies)
    if not swagger_doc:
        return "❌ API 문서를 찾을 수 없습니다."
    
    try:
        analysis = analyzer.analyze_swagger_docs(swagger_doc, url)
        
        if format.lower() == "json":
            # JSON 형식으로 내보내기
            export_data = {
                "api_info": {
                    "title": analysis.title,
                    "version": analysis.version,
                    "description": analysis.description,
                    "base_url": analysis.base_url,
                    "total_endpoints": analysis.total_endpoints
                },
                "endpoints": [
                    {
                        "path": ep.path,
                        "method": ep.method,
                        "summary": ep.summary,
                        "description": ep.description,
                        "tags": ep.tags
                    } for ep in analysis.endpoints
                ],
                "recommendations": [
                    {
                        "page": rec.page,
                        "description": rec.description,
                        "endpoints": [
                            {
                                "path": ep.path,
                                "method": ep.method,
                                "summary": ep.summary
                            } for ep in rec.endpoints
                        ]
                    } for rec in analysis.recommendations
                ]
            }
            
            return f"📄 **API 문서 내보내기 완료 (JSON)**\n\n```json\n{json.dumps(export_data, indent=2, ensure_ascii=False)}\n```"
            
        elif format.lower() == "markdown":
            # Markdown 형식으로 내보내기
            md_content = f"# {analysis.title} API 문서\n\n"
            md_content += f"**버전**: {analysis.version}\n\n"
            md_content += f"**총 엔드포인트**: {analysis.total_endpoints}개\n\n"
            
            if analysis.description:
                md_content += f"## 설명\n\n{analysis.description}\n\n"
            
            md_content += "## 엔드포인트 목록\n\n"
            for endpoint in analysis.endpoints:
                md_content += f"### {endpoint.method} {endpoint.path}\n\n"
                if endpoint.summary:
                    md_content += f"**설명**: {endpoint.summary}\n\n"
                if endpoint.tags:
                    md_content += f"**태그**: {', '.join(endpoint.tags)}\n\n"
                md_content += "---\n\n"
            
            return f"📄 **API 문서 내보내기 완료 (Markdown)**\n\n```markdown\n{md_content}\n```"
        
        else:
            return "❌ 지원하지 않는 형식입니다. 'json' 또는 'markdown'을 사용해주세요."
        
    except Exception as e:
        logger.error(f"API 문서 내보내기 중 오류: {e}")
        return f"❌ API 문서 내보내기 중 오류가 발생했습니다: {e}" 