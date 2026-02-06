# Hot Reload

Development environment with automatic code reloading.

## Overview

Hot reload enables instant feedback during development:

| Change Type | Reload Time | State Preserved |
|-------------|-------------|-----------------|
| Python (.py) | ~1 second | No |
| React (.tsx) | < 1 second | Yes |
| Tailwind (CSS) | Instant | Yes |

## Docker Development

### Start Services

```bash
# Using dev script
./dev.sh start

# Or directly
docker-compose up -d
```

### How It Works

```mermaid
flowchart LR
    Editor["Your Editor<br/>(save file)"] --> Volume["Docker Volume<br/>(sync)"]
    Volume --> Container["Container<br/>(detect)"]
    Container --> Reload["Reload Process"]
```

### Backend Hot Reload

Uvicorn watches for file changes:

```yaml
# docker-compose.yml
backend:
  volumes:
    - ./backend:/app    # Mount source code
  command: uvicorn app.main:app --reload --host 0.0.0.0
```

**Process**:

1. Save Python file
2. Docker syncs to container (~100ms)
3. Uvicorn detects change
4. Server restarts (~1 second)
5. API ready

### Frontend Hot Reload

Next.js Fast Refresh:

```yaml
# docker-compose.yml
frontend:
  volumes:
    - ./frontend:/app
    - /app/node_modules  # Exclude node_modules
    - /app/.next         # Exclude build cache
  command: pnpm dev
```

**Process**:

1. Save React file
2. Next.js detects change
3. Browser updates (< 1 second)
4. Component state preserved

## Testing Hot Reload

### Backend Test

1. Open `backend/app/main.py`
2. Find the startup log line
3. Change it slightly:

   ```python
   logger.info(f"🚀 Starting {settings.PROJECT_NAME}")
   ```

4. Save file
5. Check logs: `./dev.sh logs backend`

### Frontend Test

1. Open http://localhost:3000
2. Edit `frontend/src/app/page.tsx`
3. Change visible text
4. Save file
5. Browser updates automatically

## Troubleshooting

### Hot Reload Not Working (Backend)

**Check Uvicorn is in reload mode**:

```bash
docker-compose logs backend | grep "reloader"
# Should see: "Started reloader process using WatchFiles"
```

**Check volume mount**:

```bash
docker-compose exec backend ls -la /app
# Should show your source files
```

**Restart backend**:

```bash
docker-compose restart backend
```

### Hot Reload Not Working (Frontend)

**Check dev mode**:

```bash
docker-compose logs frontend | grep "Ready"
# Should see: "Ready in X.Xs"
```

**Clear Next.js cache**:

```bash
docker-compose exec frontend rm -rf .next
docker-compose restart frontend
```

### Slow Hot Reload

**Optimize file watching**:

Add to `.vscode/settings.json`:

```json
{
  "files.watcherExclude": {
    "**/.git/**": true,
    "**/node_modules/**": true,
    "**/.next/**": true,
    "**/__pycache__/**": true
  }
}
```

**Check Docker resources**:

```bash
docker stats
# Ensure containers have enough memory
```

## Local Development (Without Docker)

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
pnpm dev
```

Both run with hot reload enabled by default.

## Performance Optimization

### Docker Volume Performance (macOS)

Use delegated volume mounts for better performance:

```yaml
volumes:
  - ./backend:/app:delegated
```

### Exclude Unnecessary Files

Create `.dockerignore`:

```text
__pycache__
*.pyc
.git
node_modules
.next
*.log
```

### Use Named Volumes for Dependencies

```yaml
volumes:
  - ./backend:/app
  - backend_venv:/app/.venv  # Persist virtual environment
```
