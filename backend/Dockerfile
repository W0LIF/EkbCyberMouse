FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY solver ./solver
COPY data ./data

EXPOSE 8080

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "330"]
