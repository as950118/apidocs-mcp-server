# API Docs MCP Server

API 문서를 분석하여 프론트엔드 구현 방법을 추천해주는 MCP (Model Context Protocol) 서버입니다.

## 🚀 주요 기능

- **API 문서 자동 분석**: Swagger/OpenAPI JSON 또는 HTML 형태의 API 문서를 자동으로 분석
- **프론트엔드 추천**: 분석된 API를 기반으로 프론트엔드 페이지 구현 방법을 추천
- **인증 지원**: 쿠키 기반 인증이 필요한 API 문서도 분석 가능
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
    result = await session.call_tool(
        "analyze_api_docs",
        {
            "url": "https://api.example.com/swagger.json",
            "cookies": {"_oauth2_proxy": "your-auth-token"}  # 선택사항
        }
    )
    print(result.content)
```

### 도구 파라미터

- **url** (필수): 분석할 API 문서의 URL
- **cookies** (선택): 인증에 필요한 쿠키 딕셔너리

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

### 분석 결과 모델
- `APIEndpoint`: 개별 API 엔드포인트 정보
- `FrontendRecommendation`: 페이지별 API 추천
- `AnalysisResult`: 전체 분석 결과

## 🎯 프론트엔드 추천 로직

서버는 다음과 같은 기준으로 API를 그룹화하여 추천합니다:

- **사용자 관리**: `user`, `member` 키워드 포함
- **인증/로그인**: `auth`, `login` 키워드 포함
- **데이터 조회**: GET 메서드
- **데이터 생성/수정**: POST, PUT, PATCH 메서드
- **파일 업로드**: 파일 관련 키워드
- **검색**: 검색 관련 키워드
- **통계/분석**: 통계 관련 키워드

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