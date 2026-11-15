FROM rust:1-slim-trixie AS native-build
WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY templates ./templates
COPY static ./static
RUN cargo build --release --locked

# Optional maintenance image; never used by the serving image.
FROM python:3.14-slim AS update
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH \
    DLFILTER_DATA_DIR=/data PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --extra update --no-dev --no-install-project
COPY initial.py ./
COPY module ./module
ENTRYPOINT ["python", "initial.py"]

FROM python:3.12-slim-trixie AS helper-build
WORKDIR /build
RUN pip install --no-cache-dir pyinstaller==6.16.0 certifi==2026.7.22
COPY scripts/title_helper.py scripts/title_helper.py
COPY module/title_lookup.py module/title_lookup.py
RUN python -m PyInstaller --onefile --name dlfilter-titles --paths . scripts/title_helper.py

FROM debian:trixie-slim AS serve
RUN useradd --create-home --uid 10001 dlfilter \
    && mkdir /presets /cache && chown dlfilter:dlfilter /presets /cache
WORKDIR /app
COPY --from=native-build /build/target/release/dlfilter /usr/local/bin/dlfilter
COPY --from=helper-build /build/dist/dlfilter-titles /app/bin/dlfilter-titles
COPY static ./static
COPY templates ./templates
ENV DLFILTER_ROOT=/app DLFILTER_DATA_DIR=/data DLFILTER_PRESETS_DIR=/presets \
    DLFILTER_CACHE_DIR=/cache DLFILTER_HOST=0.0.0.0 DLFILTER_PORT=8000
USER dlfilter
EXPOSE 8000
VOLUME ["/data", "/presets", "/cache"]
CMD ["dlfilter", "serve"]
