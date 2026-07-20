FROM python:3.14.0-slim@sha256:5af4c7f950774a1abf3fd4e8e3fc95f4d0fe684c7fdc1eb10777fc5a017371c7

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app

COPY vendor/runtime-requirements.lock.txt vendor/runtime-requirements.lock.txt
COPY vendor/cache/python/linux-x86_64 vendor/cache/python/linux-x86_64
COPY dist/*.whl dist/

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --disable-pip-version-check --require-hashes --no-index --find-links vendor/cache/python/linux-x86_64 -r vendor/runtime-requirements.lock.txt && \
    /opt/venv/bin/pip install --disable-pip-version-check --no-deps --no-index dist/*.whl && \
    rm -rf /root/.cache

USER app
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=2s --start-period=2s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1).read()"]

ENTRYPOINT ["python-template"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
