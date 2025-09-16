FROM ghcr.io/astral-sh/uv:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app

COPY ./pyproject.toml /app/pyproject.toml
COPY ./README.md /app/README.md

COPY ./start.py /app/start.py
COPY ./app /app/app
RUN uv sync

EXPOSE 8000

CMD ["uv", "run",  "start.py"] 


