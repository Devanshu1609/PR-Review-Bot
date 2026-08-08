FROM python:3.11-slim

WORKDIR /app

# Install minimal system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY entrypoint.sh /app/entrypoint.sh
COPY .mifoshawk.yml.example /app/.mifoshawk.yml.example
COPY README.md /app/README.md
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
