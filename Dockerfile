FROM python:3.12-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /tmp/linkindir && chmod 777 /tmp/linkindir
ENV PORT=8000
EXPOSE 8000 7860
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
