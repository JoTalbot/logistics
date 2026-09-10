FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml .
COPY backend ./backend

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER 10001:10001
EXPOSE 8000

CMD ["uvicorn", "logistics.review_extensions:app", "--host", "0.0.0.0", "--port", "8000"]
