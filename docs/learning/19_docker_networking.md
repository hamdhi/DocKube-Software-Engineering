# Docker and Networking Quick Reference

## Docker Commands You Actually Use
```
docker build -t myapp .          # Build image
docker run -p 8000:8000 myapp    # Run container
docker ps                        # List running containers
docker ps -a                     # List all containers
docker logs -f container_name    # Follow logs
docker exec -it container_name bash  # Enter container
docker stop container_name       # Stop container
docker rm container_name         # Remove container
docker rmi image_name            # Remove image
docker compose up -d             # Start all services
docker compose down              # Stop all services
docker system prune -a           # Clean everything unused
```

## Dockerfile Best Practices
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose (Full Stack)
```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/mydb
    depends_on: [db]

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]

volumes:
  pgdata:
```

## Key Networking Concepts
```
CONTAINER NETWORK:
  Containers on same Docker network can reach each other by SERVICE NAME
  app --> http://db:5432 (NOT localhost:5432!)

PORT MAPPING:
  -p HOST:CONTAINER
  -p 8000:8000 means your machine's port 8000 maps to container's port 8000

VOLUMES:
  -v pgdata:/var/lib/postgresql/data  # Named volume (survives container restart)
  -v ./code:/app                      # Bind mount (live reload during dev)

ENVIRONMENT:
  environment:                        # In compose
    - KEY=value
  --env-file .env                     # In docker run
```

## Common Ports
```
8000    FastAPI / Python web
3000    React / Node.js frontend
5432    PostgreSQL
3306    MySQL
27017   MongoDB
6379    Redis
80/443  Nginx / HTTP/HTTPS
```

## Troubleshooting
```
"Connection refused"     --> Check if service is on same Docker network
"Port already in use"    --> Another process is using that port on your machine
"Module not found"       --> Missing in requirements.txt or need to rebuild
"Permission denied"      --> Use USER appuser in Dockerfile, or check file ownership
```
