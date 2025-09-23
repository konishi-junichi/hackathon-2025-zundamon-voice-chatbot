# A2A Agent Dockerfile

FROM python:3.13-slim

# ビルドツール（g++など）をインストール
# これにより、madokaのようなC/C++拡張を持つパッケージのビルドが可能になります。
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

EXPOSE 8080

WORKDIR /app

COPY . ./

# uv sync の前にビルドツールがインストールされている必要があります
RUN uv sync

ENTRYPOINT ["uv", "run", ".", "--host", "0.0.0.0", "--port", "8080"]