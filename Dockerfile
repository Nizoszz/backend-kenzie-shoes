FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --requirement requirements.txt

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
RUN groupadd --system django && useradd --system --gid django --home /app django
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=django:django . .
RUN SECRET_KEY=container-build-only \
    DEBUG=false \
    DATABASE_URL=sqlite:////tmp/container-build.sqlite3 \
    ALLOWED_HOSTS=localhost \
    SECURE_SSL_REDIRECT=false \
    python manage.py collectstatic --noinput
USER django
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/health/', timeout=3)"
CMD ["sh", "-c", "python manage.py migrate --noinput && if [ \"${SEED_DEMO_PRODUCTS:-false}\" = \"true\" ]; then python manage.py seed_shoes; fi && exec gunicorn _core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --no-control-socket --access-logfile - --error-logfile -"]
