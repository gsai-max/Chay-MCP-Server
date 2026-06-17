FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY google-mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server files
COPY google-mcp-server/ .

# Run uvicorn
ENV PORT=8000
EXPOSE 8000

CMD ["python", "server.py"]
