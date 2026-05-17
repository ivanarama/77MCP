FROM mirror.gcr.io/library/python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

RUN mkdir -p /data

EXPOSE 8099

CMD ["python", "-m", "mcp_1c77"]
