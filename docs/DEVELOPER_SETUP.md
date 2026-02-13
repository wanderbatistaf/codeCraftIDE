# Developer Setup Guide

This guide covers local development for CodeCraft Studio (Next.js) and the Python API backend.

## Prerequisites

- Docker 20.10+
- Docker Compose
- Git

## Quick Start (Docker)

```bash
git clone https://github.com/wanderbatistaf/fglInterpreter.git
cd fglInterpreter
docker compose up --build
```

Services:

- Studio: http://localhost:9002
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## Manual Setup

### Backend

```bash
pip install -e ".[api]"
python -m fglinterpreter.api.main
```

### Studio

```bash
cd studio
npm install
npm run dev
```

## Testing

### Backend

```bash
pytest
pytest tests/unit -v
```

### Studio

```bash
cd studio
npm run lint
npm run typecheck
```

## Useful Docker Commands

```bash
docker compose up
docker compose up --build
docker compose down
docker compose logs -f
docker compose logs -f backend
docker compose logs -f studio
```

## Troubleshooting

### Ports in use

- Studio uses `9002`
- API uses `8000`

Adjust host ports in `docker-compose.yml` if needed.

### Dependency changes

If `pyproject.toml` or `studio/package.json` changes:

```bash
docker compose up --build
```

## References

- Project README: `README.md`
- Studio docs: `studio/Documentation/en-us/Manual.md`
