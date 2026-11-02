FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# app/config.py reads these. "db" is mapped to the database host's private IP
# by extra_hosts in infra/ansible/templates/backend-compose.yml.j2.
ENV MONGODB_HOST=db \
    MONGODB_DB=skipq

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]