FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    psycopg2-binary \
    pandas \
    python-dotenv \
    apscheduler \
    pytz

COPY DBtoDB.py /app/DBtoDB.py

CMD ["python", "/app/DBtoDB.py"]
