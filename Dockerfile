FROM python:3.11-slim AS builder
WORKDIR /install
RUN apt-get update && apt-get install -y build-essential --no-install-recommends && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt -t /install/packages

FROM python:3.11-slim
ENV TZ=UTC
WORKDIR /app
RUN apt-get update && apt-get install -y cron tzdata ca-certificates --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && echo UTC > /etc/timezone
COPY --from=builder /install/packages /usr/local/lib/python3.11/site-packages
COPY . /app
RUN mkdir -p /data /cron
RUN chmod 700 /data /cron || true
RUN chmod 600 /app/student_private.pem || true
RUN chmod 644 /app/student_public.pem /app/instructor_public.pem || true
RUN chmod +x /app/start.sh || true
COPY cron/2fa-cron /etc/cron.d/2fa-cron
RUN chmod 0644 /etc/cron.d/2fa-cron
RUN crontab /etc/cron.d/2fa-cron
EXPOSE 8080
CMD ["./start.sh"]
