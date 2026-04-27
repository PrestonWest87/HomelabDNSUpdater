FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r ddnsuser && useradd -r -g ddnsuser ddnsuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dynamic_dns.py .

RUN chown -R ddnsuser:ddnsuser /app
USER ddnsuser

# Removed the hardcoded GOOGLE_APPLICATION_CREDENTIALS environment variable.
# It should now be passed via docker-compose or the docker run command.

CMD ["python3", "dynamic_dns.py"]
