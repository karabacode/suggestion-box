FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY suggestion-core/app ./app
COPY ./schemas ./app/schemas

RUN python3 ./app/schemas/compile_protos.py --skip-sync
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
