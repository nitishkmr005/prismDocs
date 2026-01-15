# Docker Setup Guide

This guide explains how to run the Document Generator application using Docker.

## Prerequisites

- Docker installed (version 20.10 or higher)
- Docker Compose installed (version 2.0 or higher)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

Run both frontend and backend together:

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the application:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Individual Services

**Backend Only:**

```bash
cd backend
docker build -t doc-generator-backend .
docker run -p 8000:8000 doc-generator-backend
```

**Frontend Only:**

```bash
cd frontend
docker build -t doc-generator-frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  doc-generator-frontend
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Optional: API keys as fallback (users can provide their own in UI)
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Backend
ENVIRONMENT=development

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then run with:

```bash
docker-compose --env-file .env up
```

### Development Mode

For development with hot-reload:

```bash
# Backend with volume mount
docker-compose up backend

# Frontend with volume mount
docker-compose up frontend
```

## Docker Commands Cheat Sheet

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose stop

# Remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# View logs
docker-compose logs -f [service_name]

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# Rebuild specific service
docker-compose up --build backend
```

## Troubleshooting

### Port Already in Use

```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Backend
  - "3001:3000"  # Frontend
```

### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R $(id -u):$(id -g) backend/data
```

### Container Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check health
docker-compose ps
```

### Clean Rebuild

```bash
# Remove everything and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Production Deployment

For production, use individual Dockerfiles with proper secrets management:

```bash
# Build for production
docker build -t doc-generator-backend:prod ./backend
docker build -t doc-generator-frontend:prod ./frontend

# Run with production settings
docker run -d \
  --name backend \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  doc-generator-backend:prod

docker run -d \
  --name frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  doc-generator-frontend:prod
```

## Health Checks

Both services include health checks:

- Backend: `GET /api/health`
- Frontend: `GET /` (homepage)

Check health status:

```bash
docker-compose ps
```

## Volumes

Backend data is persisted in a Docker volume:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect doc-gen-frontend_backend-data

# Backup volume
docker run --rm -v doc-gen-frontend_backend-data:/data \
  -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data
```
