FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8080

WORKDIR /app
COPY . ./
RUN pip install -r requirements.txt

ENTRYPOINT ["adk", "web", "--host=0.0.0.0", "--port=8080"]