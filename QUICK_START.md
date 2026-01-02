# Coda Agent - Quick Start Guide

## Welcome to Coda Agent Development! 🚀

This guide will help you get started with developing the Coda Agent module.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (v20.10+) - [Download](https://www.docker.com/products/docker-desktop)
- **Git** - [Download](https://git-scm.com/downloads)
- **Node.js** (v18+) - [Download](https://nodejs.org/)
- **Python** (v3.11+) - [Download](https://www.python.org/downloads/)
- **Code Editor** - VS Code recommended

## Project Structure

```
coda-agent/
├── backend/                    # FastAPI backend (to be created)
├── frontend/                   # React frontend (to be created)
├── observability/              # Monitoring configs (to be created)
├── docs/                       # Documentation
│   ├── PRODUCT_PLAN.md        # ✅ Complete roadmap
│   ├── TECHNICAL_SPEC.md      # ✅ Architecture details
│   ├── BACKLOG.md             # ✅ Feature breakdown
│   └── IMPLEMENTATION_SUMMARY.md # ✅ Overview
├── docker-compose.yml          # ✅ Container orchestration
├── .env.example                # ✅ Environment template
├── .gitignore                  # ✅ Git ignore rules
└── README.md                   # ✅ Project README
```

## Quick Start (5 Minutes)

### 1. Clone and Setup

```bash
# Clone the repository (when available)
git clone <repository-url>
cd coda-agent

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` and add your API keys:

```bash
# Minimum required for MVP
OPENAI_API_KEY=sk-your-key-here
MCP_SERVER_URL=http://your-mcp-server:8080

# Optional: Change default passwords
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

### 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686

## Development Workflow

### Backend Development

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Frontend Development

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Current Sprint (Sprint 1)

### Goal
Setup project foundation and basic infrastructure

### Stories in Progress
1. **Setup Project Structure** (3 points)
   - ✅ Documentation created
   - ⏳ Backend scaffolding
   - ⏳ Frontend scaffolding

2. **Backend API Foundation** (5 points)
   - ⏳ FastAPI setup
   - ⏳ Database models
   - ⏳ Basic CRUD endpoints

3. **Frontend Scaffolding** (5 points)
   - ⏳ React + TypeScript setup
   - ⏳ TailwindCSS configuration
   - ⏳ Component library

4. **LLM Integration - OpenAI** (8 points)
   - ⏳ OpenAI client
   - ⏳ Streaming support
   - ⏳ Token counting

### Next Steps
1. Create backend directory structure
2. Initialize FastAPI application
3. Setup database models
4. Create frontend with Vite
5. Implement basic chat interface

## Key Documents to Review

### For Everyone
- **[README.md](./README.md)** - Project overview and quick reference
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - High-level summary

### For Product/Planning
- **[PRODUCT_PLAN.md](./PRODUCT_PLAN.md)** - Complete roadmap with sprints
- **[BACKLOG.md](./BACKLOG.md)** - Detailed feature breakdown

### For Development
- **[TECHNICAL_SPEC.md](./TECHNICAL_SPEC.md)** - Architecture and implementation details

## Development Best Practices

### Code Style

**Backend (Python)**:
```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

**Frontend (TypeScript)**:
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/F1.1-multi-llm-router

# Make changes and commit
git add .
git commit -m "feat: implement OpenAI provider"

# Push and create PR
git push origin feature/F1.1-multi-llm-router
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Testing

**Backend**:
```python
# Unit test example
def test_openai_provider():
    provider = OpenAIProvider(api_key="test")
    assert provider.model_name == "gpt-4"

# Integration test example
async def test_chat_endpoint(client):
    response = await client.post("/api/v1/chat/stream", json={
        "session_id": "test-session",
        "content": "Hello"
    })
    assert response.status_code == 200
```

**Frontend**:
```typescript
// Component test example
test('renders chat interface', () => {
  render(<ChatInterface sessionId="test" />);
  expect(screen.getByText('Send')).toBeInTheDocument();
});
```

## Common Commands

### Docker

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild services
docker-compose up -d --build

# View logs
docker-compose logs -f [service-name]

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# Clean up
docker-compose down -v  # Remove volumes
docker system prune -a  # Clean all unused resources
```

### Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U coda -d coda_agent

# Backup database
docker-compose exec postgres pg_dump -U coda coda_agent > backup.sql

# Restore database
docker-compose exec -T postgres psql -U coda coda_agent < backup.sql

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Redis

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Clear all cache
docker-compose exec redis redis-cli FLUSHALL

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR
```

## Troubleshooting

### Issue: Docker containers won't start

**Solution**:
```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose up -d --build

# Check disk space
docker system df
```

### Issue: Database connection error

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify connection string in .env
echo $DATABASE_URL
```

### Issue: Port already in use

**Solution**:
```bash
# Find process using port (example: 8000)
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

### Issue: Frontend can't connect to backend

**Solution**:
```bash
# Check CORS settings in backend
# Verify VITE_API_URL in frontend .env
# Check network in docker-compose.yml
```

## Useful Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Docker Docs](https://docs.docker.com/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [TablePlus](https://tableplus.com/) - Database GUI
- [Redis Insight](https://redis.com/redis-enterprise/redis-insight/) - Redis GUI

### Learning
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [React Tutorial](https://react.dev/learn)
- [Docker Tutorial](https://docs.docker.com/get-started/)

## Team Communication

### Daily Standup (15 min)
- What did you do yesterday?
- What will you do today?
- Any blockers?

### Sprint Planning (2 hours)
- Review backlog
- Estimate stories
- Commit to sprint goals

### Sprint Review (1 hour)
- Demo completed features
- Gather feedback
- Update roadmap

### Sprint Retrospective (1 hour)
- What went well?
- What can improve?
- Action items

## Getting Help

### Internal
- **Slack**: #coda-agent-dev
- **Wiki**: [Internal Wiki Link]
- **Team Lead**: [Name]

### External
- **GitHub Issues**: For bugs and feature requests
- **Stack Overflow**: Tag with `coda-agent`
- **Discord**: [Community Link]

## Next Steps for New Developers

1. **Day 1**: Setup development environment
   - [ ] Install prerequisites
   - [ ] Clone repository
   - [ ] Run `docker-compose up`
   - [ ] Access all services

2. **Day 2**: Explore codebase
   - [ ] Read all documentation
   - [ ] Review architecture
   - [ ] Understand data models
   - [ ] Run existing tests

3. **Day 3**: First contribution
   - [ ] Pick a small story
   - [ ] Create feature branch
   - [ ] Implement and test
   - [ ] Submit PR

4. **Week 1**: Join sprint
   - [ ] Attend sprint planning
   - [ ] Commit to stories
   - [ ] Daily standups
   - [ ] Pair programming

## Sprint 1 Checklist

### Setup Tasks
- [ ] Create backend directory structure
- [ ] Initialize FastAPI application
- [ ] Setup database with Alembic
- [ ] Create frontend with Vite
- [ ] Configure TailwindCSS
- [ ] Setup testing frameworks
- [ ] Configure CI/CD pipeline

### Development Tasks
- [ ] Implement database models
- [ ] Create API endpoints
- [ ] Build chat interface
- [ ] Integrate OpenAI
- [ ] Add session management
- [ ] Write tests

### Documentation Tasks
- [ ] API documentation
- [ ] Component documentation
- [ ] Deployment guide
- [ ] Contributing guide

## Success Criteria for Sprint 1

- [ ] All services running in Docker
- [ ] Database migrations working
- [ ] Basic API endpoints functional
- [ ] Chat interface renders
- [ ] OpenAI integration working
- [ ] Tests passing (>80% coverage)
- [ ] Documentation complete

---

**Happy Coding! 🎉**

If you have any questions, don't hesitate to ask the team!
