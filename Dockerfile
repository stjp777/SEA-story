FROM python:3.13-slim
WORKDIR /app
COPY app.py index.html data.json ./
# Ollama runs on the host; host.docker.internal reaches it from Docker Desktop
ENV HOST=0.0.0.0 \
    OLLAMA_URL=http://host.docker.internal:11434 \
    PYTHONUNBUFFERED=1
RUN useradd -m app
USER app
EXPOSE 8000
CMD ["python", "app.py"]
