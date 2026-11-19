FROM python:3.12-slim

WORKDIR /app

# Install system dependencies & Tectonic
RUN apt-get update && apt-get install -y \
    curl \
    libssl-dev \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -fsSL \
    https://drop.science/tectonic/install.sh | sh && \
    (mv /root/.tectonic/bin/tectonic /usr/local/bin/tectonic || true)

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p latex/output static

EXPOSE 8000 8001

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 & python mcp_server.py"]
