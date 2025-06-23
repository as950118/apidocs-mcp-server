# 1. 공식 Python 런타임 이미지를 기반으로 시작합니다.
FROM python:3.11-slim

# 2. 환경 변수 설정
#    - PYTHONDONTWRITEBYTECODE: 파이썬이 .pyc 파일을 만들지 않도록 합니다.
#    - PYTHONUNBUFFERED: 컨테이너 로그가 지연 없이 바로 스트리밍되도록 합니다.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. 애플리케이션 코드를 위한 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 설치를 위한 파일과 소스 코드 복사
#    - pyproject.toml과 src 디렉토리를 먼저 복사합니다.
#    - 이 순서는 `pip install .`이 소스 코드를 찾을 수 있도록 보장합니다.
COPY pyproject.toml README.md ./
COPY src/ /app/src

# 5. 의존성과 프로젝트 패키지를 설치합니다.
#    - `pip install .` 명령어는 pyproject.toml을 읽어 의존성을 설치하고
#    - src 디렉토리의 코드를 패키지로 설치합니다.
RUN pip install --no-cache-dir .

# 6. 컨테이너가 리슨할 포트 지정
EXPOSE 8080

# 7. 컨테이너 시작 시 실행될 기본 명령어 정의
#    - `mcp run`을 사용하여 FastMCP 서버를 실행합니다.
#    - `api_docs_mcp_server:server`는 api_docs_mcp_server 패키지의 server 객체를 의미합니다.
#    - `--host 0.0.0.0`은 컨테이너 외부에서 접근 가능하도록 합니다.
#    - Smithery가 제공하는 $PORT 환경 변수를 사용합니다.
CMD ["sh", "-c", "mcp run api_docs_mcp_server:server --host 0.0.0.0 --port $PORT"] 