# Check if .env exists, if not copy from example
if (-not (Test-Path .env)) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item .env.example .env
}

# Build and start Docker containers
Write-Host "Starting Coda Agent dev environment..."
docker-compose up -d --build

# Wait for services to be ready
Write-Host "Waiting for services to initialize..."
Start-Sleep -Seconds 10

# Show status
docker-compose ps

Write-Host "`nApplications are running at:"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8000/docs"
Write-Host "Grafana:  http://localhost:3001"
