# API Docs MCP Server

API 문서를 분석하여 프론트엔드 구현 방법을 추천해주는 MCP (Model Context Protocol) 서버입니다.

## 🚀 주요 기능

- **API 문서 자동 분석**: Swagger/OpenAPI JSON 또는 HTML 형태의 API 문서를 자동으로 분석
- **프론트엔드 추천**: 분석된 API를 기반으로 프론트엔드 페이지 구현 방법을 추천
- **인증 지원**: 쿠키 기반 인증이 필요한 API 문서도 분석 가능
- **API 상태 확인**: 엔드포인트의 상태와 응답 시간을 확인
- **코드 예시 생성**: JavaScript/TypeScript, Python 코드 예시 자동 생성
- **엔드포인트 검색**: 키워드 기반 API 엔드포인트 검색
- **문서 내보내기**: JSON, Markdown 형식으로 API 문서 내보내기
- **FastMCP 기반**: 최신 FastMCP 규격을 사용하여 빠르고 효율적인 서버 구현

## 📋 지원하는 API 문서 형식

- **Swagger/OpenAPI JSON**: `/swagger.json`, `/api-docs`, `/openapi.json` 등
- **HTML 문서**: Swagger UI 등이 포함된 HTML 페이지
- **인증이 필요한 문서**: 쿠키 기반 인증 지원

## 🛠️ 설치 및 실행

### 로컬 개발 환경

1. **의존성 설치**
   ```bash
   pip install -e .
   ```

2. **서버 실행**
   ```bash
   mcp run api_docs_mcp_server:server
   ```

### Docker를 사용한 실행

1. **이미지 빌드**
   ```bash
   docker build -t api-docs-mcp-server .
   ```

2. **컨테이너 실행**
   ```bash
   docker run -p 8080:8080 api-docs-mcp-server
   ```

### Smithery 배포

이 프로젝트는 Smithery 플랫폼에 배포할 수 있도록 구성되어 있습니다:

1. **Smithery CLI 설치**
   ```bash
   npm install -g @smithery/cli
   ```

2. **배포**
   ```bash
   smithery deploy
   ```

## 🔧 사용 방법

### MCP 클라이언트에서 사용

```python
# MCP 클라이언트 예시
from mcp.client import ClientSession

async with ClientSession("http://localhost:8080") as session:
    # API 문서 분석
    result = await session.call_tool(
        "analyze_api_docs",
        {
            "url": "https://api.example.com/swagger.json",
            "cookies": {"_oauth2_proxy": "your-auth-token"}  # 선택사항
        }
    )
    print(result.content)
    
    # API 상태 확인
    health_result = await session.call_tool(
        "health_check_api",
        {
            "url": "https://api.example.com/swagger.json",
            "max_endpoints": 5
        }
    )
    print(health_result.content)
    
    # 코드 예시 생성
    code_result = await session.call_tool(
        "generate_code_examples",
        {
            "url": "https://api.example.com/swagger.json",
            "endpoint_path": "/api/users"
        }
    )
    print(code_result.content)
```

## 🛠️ 사용 가능한 도구들

### 1. `analyze_api_docs`
API 문서를 분석하여 프론트엔드 페이지 구현 방법을 추천합니다.

**파라미터:**
- `url` (필수): 분석할 API 문서의 URL
- `cookies` (선택): 인증에 필요한 쿠키 딕셔너리

### 2. `get_api_endpoints`
API 문서에서 모든 엔드포인트 목록을 가져옵니다.

**파라미터:**
- `url` (필수): 분석할 API 문서의 URL
- `cookies` (선택): 인증에 필요한 쿠키 딕셔너리

### 3. `health_check_api`
API 엔드포인트들의 상태를 확인합니다.

**파라미터:**
- `url` (필수): API 문서의 URL
- `cookies` (선택): 인증에 필요한 쿠키 딕셔너리
- `max_endpoints` (선택): 테스트할 최대 엔드포인트 수 (기본값: 10)

### 4. `generate_code_examples`
특정 API 엔드포인트에 대한 코드 예시를 생성합니다.

**파라미터:**
- `url` (필수): API 문서의 URL
- `endpoint_path` (필수): 코드 예시를 생성할 엔드포인트 경로
- `cookies` (선택): 인증에 필요한 쿠키 딕셔너리

### 5. `search_endpoints`
API 엔드포인트에서 특정 키워드를 검색합니다.

**파라미터:**
- `url` (필수): API 문서의 URL
- `search_term` (필수): 검색할 키워드
- `cookies` (선택): 인증에 필요한 쿠키 딕셔너리

### 6. `get_api_info`
API 문서의 기본 정보를 가져옵니다.

**파라미터:**
- `url` (필수): API 문서의 URL
- `cookies` (선택): 인증에 필요한 쿠키 딕셔너리

### 7. `export_api_docs`
API 문서를 다양한 형식으로 내보냅니다.

**파라미터:**
- `url` (필수): API 문서의 URL
- `format` (선택): 내보낼 형식 (json, markdown) (기본값: json)
- `cookies` (선택): 인증에 필요한 쿠키 딕셔너리

## 📊 분석 결과 예시

```
✅ **API 문서 분석 완료: Example API (1.0.0)**

총 25개의 API 엔드포인트를 발견했습니다.

--- 📄 프론트엔드 페이지 구현 추천 ---

### 💡 사용자 관리 페이지
_사용자 관리 기능 구현을 위한 API들_
- `GET` /api/users (사용자 목록 조회)
- `POST` /api/users (새 사용자 생성)
- `PUT` /api/users/{id} (사용자 정보 수정)
- `DELETE` /api/users/{id} (사용자 삭제)

### 💡 인증/로그인 페이지
_인증/로그인 기능 구현을 위한 API들_
- `POST` /api/auth/login (로그인)
- `POST` /api/auth/logout (로그아웃)
- `GET` /api/auth/me (현재 사용자 정보)

### 💡 결제/결제 페이지
_결제/결제 기능 구현을 위한 API들_
- `POST` /api/payments (결제 생성)
- `GET` /api/payments/{id} (결제 정보 조회)
- `PUT` /api/payments/{id}/cancel (결제 취소)
```

## 🏗️ 프로젝트 구조

```
apidocs-mcp-server/
├── src/
│   └── api_docs_mcp_server/
│       └── __init__.py
├── server.py              # 메인 서버 파일
├── pyproject.toml         # 프로젝트 설정
├── Dockerfile            # Docker 설정
├── smithery.yaml         # Smithery 배포 설정
└── README.md             # 이 파일
```

## 🔍 주요 클래스 및 기능

### APIDocsAnalyzer
- `fetch_swagger_docs()`: Swagger/OpenAPI JSON 문서 가져오기
- `fetch_html_docs()`: HTML 형태의 API 문서 가져오기
- `analyze_swagger_docs()`: API 문서 분석 및 구조화
- `_generate_frontend_recommendations()`: 프론트엔드 추천 생성
- `health_check_endpoint()`: 개별 엔드포인트 상태 확인
- `generate_code_examples()`: 코드 예시 생성

### 분석 결과 모델
- `APIEndpoint`: 개별 API 엔드포인트 정보
- `FrontendRecommendation`: 페이지별 API 추천
- `AnalysisResult`: 전체 분석 결과
- `APIHealthCheck`: API 상태 확인 결과
- `CodeExample`: 코드 예시 모델

## 🎯 프론트엔드 추천 로직

서버는 다음과 같은 기준으로 API를 그룹화하여 추천합니다:

- **사용자 관리**: `user`, `member`, `customer` 키워드 포함
- **인증/로그인**: `auth`, `login`, `token`, `oauth` 키워드 포함
- **결제/결제**: `payment`, `pay`, `billing`, `charge` 키워드 포함
- **파일 업로드**: `upload`, `file`, `image`, `media` 키워드 포함
- **검색**: `search`, `find`, `query` 키워드 포함
- **통계/분석**: `stats`, `analytics`, `report`, `metric` 키워드 포함
- **알림/메시지**: `notification`, `message`, `alert`, `push` 키워드 포함
- **설정/관리**: `config`, `setting`, `admin`, `management` 키워드 포함
- **데이터 조회**: GET 메서드
- **데이터 생성/수정**: POST, PUT, PATCH 메서드

## 🔧 개발 환경 설정

### 필수 요구사항
- Python 3.10 이상
- pip

### 개발 의존성 설치
```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -e .
```

### 테스트
```bash
# 서버 실행 테스트
mcp run api_docs_mcp_server:server --host 0.0.0.0 --port 8080
```

## 📝 라이선스

MIT License

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**참고**: 이 서버는 FastMCP 규격을 사용하여 구현되었으며, Smithery 플랫폼과 호환됩니다.