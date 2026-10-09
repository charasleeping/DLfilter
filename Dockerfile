# Serves DLfilter from a database directory mounted at /data.
# Nothing is downloaded or crawled at startup.
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv

# Set WITH_UPDATE=1 to also install the dependencies of initial.py (crawler and embedding model).
ARG WITH_UPDATE=0

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DLFILTER_DATA_DIR=/data \
    DLFILTER_PRESETS_DIR=/presets \
    DLFILTER_HOST=0.0.0.0 \
    DLFILTER_PORT=8000

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN if [ "$WITH_UPDATE" = "1" ]; then extras="--extra update"; else extras=""; fi \
    && uv sync --locked --no-dev --no-install-project $extras \
    && rm -rf /root/.cache

COPY app.py initial.py ./
COPY module ./module
COPY static ./static
COPY templates ./templates

RUN useradd --create-home --uid 10001 dlfilter \
    && mkdir /presets && chown dlfilter:dlfilter /presets
USER dlfilter

EXPOSE 8000
VOLUME ["/data", "/presets"]
CMD ["python", "app.py"]
