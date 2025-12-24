FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY wheels /wheels
RUN pip install --no-cache-dir -r /app/requirements.txt

# 소스 복사
COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]