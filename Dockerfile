FROM python:3.11-slim AS builder
WORKDIR /install
RUN apt-get update && apt-get install -y build-essential --no-install-recommends && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m pip install --upgrade pip
# install into a wheel cache to speed final install (builder will prepare wheels)
RUN python -m pip wheel --no-deps --wheel-dir /install/wheels -r requirements.txt

FROM python:3.11-slim
ENV TZ=UTC
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y cron tzdata ca-certificates gcc --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && echo UTC > /etc/timezone

# Copy wheels from builder and install them so console scripts are available
COPY --from=builder /install/wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* || python -m pip install --no-cache-dir -r requirements.txt

# App files and permissions
COPY . /app
RUN mkdir -p /data /cron
RUN chmod 700 /data /cron || true
RUN chmod 600 /app/student_private.pem || true
RUN chmod 644 /app/student_public.pem /app/instructor_public.pem || true
RUN chmod +x /app/start.sh || true

# Install cron job file
COPY cron/2fa-cron /etc/cron.d/2fa-cron
RUN chmod 0644 /etc/cron.d/2fa-cron

EXPOSE 8080
CMD ["./start.sh"]
