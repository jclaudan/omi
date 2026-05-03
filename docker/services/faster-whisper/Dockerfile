FROM python:3.11-slim AS builder

ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv

COPY docker/services/faster-whisper/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


FROM python:3.11-slim

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"

# FFmpeg required for audio decoding (MP3, OGG, OPUS, WEBM, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY docker/services/faster-whisper/main.py .

EXPOSE 8001
CMD ["python", "main.py"]
