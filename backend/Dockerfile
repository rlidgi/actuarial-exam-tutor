FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY migrations/ migrations/
COPY wsgi.py .

ENV FLASK_APP=wsgi.py

EXPOSE 8000
# flask db upgrade is idempotent (no-ops once the DB is already at head), so
# running it on every container start keeps prod schema in sync with
# whatever migration shipped alongside this image, with no separate manual
# step required after a deploy.
CMD ["sh", "-c", "flask db upgrade && exec gunicorn --bind 0.0.0.0:8000 --workers 8 --timeout 120 wsgi:app"]
