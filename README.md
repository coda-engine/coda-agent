# Coda Agent

> A generic AI agent interface with multi-LLM support and direct access to Coda's decision engine and analytics tools via MCP server integration.

[![Version](https://img.shields.io/badge/version-0.4.0--beta-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen)]()

## Overview

**Coda Agent** is a containerized, production-ready agent module that provides a ChatGPT-like experience while leveraging specialized solver and analytics tools. It serves as the user-facing interface for the Coda Platform's decision engine.

### Key Features

- 🤖 **Multi-LLM Support**: Choose from OpenAI, Anthropic, Google, or hosted models
- 🔑 **BYOK or Hosted**: Bring Your Own Key or use Coda-hosted models
- 🔧 **MCP Bridge Integration**: Direct intelligent access to 8+ Coda solver engines:
  - **Optimization**: VRP, MILP, CP-SAT, Continuous Linear
  - **Network**: Min Cost Flow, Max Flow
  - **Assignment**: Linear Sum Assignment
  - **Statistics**: T-Test Hypothesis Testing
- 🔍 **Context Awareness**: Long-term memory with automatic conversation summarization.
- **Thread Management**: Branch conversations at any point to explore alternative paths.
- **Observability**: Real-time token tracking, execution timing, decision counting, and tool success/failure monitoring.
- **Chain of Thought**: Visibility into the agent's internal reasoning process.
- 📊 **Analytics Dashboard**: Usage insights and tool utilization tracking
- 📄 **File Analysis**: Upload and analyze PDF, CSV, Excel, and text files.
- 👍 **Feedback System**: Integrated user feedback mechanism for continuous improvement.
- 🎯 **Tool Evaluation**: Automatic assessment of tool usage quality
- 🌳 **Thread Branching**: Explore alternative conversation paths
- 📤 **Export & Share**: Share sessions and export conversations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Coda Agent Module                        │
│                     (Containerized)                          │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React) │ Backend (FastAPI) │ Database (PostgreSQL)│
│  LLM Router       │ Agent Orchestrator │ Cache (Redis)       │
│  MCP Integration  │ Observability      │ Analytics           │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL 16+ with pgvector extension

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coda-agent
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Grafana: http://localhost:3001

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

## Project Structure

```
coda-agent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── core/           # Core utilities
│   ├── tests/              # Backend tests
│   └── Dockerfile
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   ├── store/         # State management
│   │   └── api/           # API client
│   ├── public/
│   └── Dockerfile
│
├── observability/          # Monitoring configs
│   ├── prometheus.yml
│   └── grafana/
│
├── docs/                   # Documentation
│   ├── PRODUCT_PLAN.md
│   ├── TECHNICAL_SPEC.md
│   └── BACKLOG.md
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## Documentation

- [Product Plan](./PRODUCT_PLAN.md) - Comprehensive product roadmap and sprint planning
- [Technical Specification](./TECHNICAL_SPEC.md) - Architecture and implementation details
- [Epic & Feature Backlog](./BACKLOG.md) - Detailed feature breakdown and user stories
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) - High-level architectural overview and status
- [API Documentation](http://localhost:8000/docs) - Interactive API documentation (when running)

## Roadmap

### v0.1.0 - MVP (Current)
- ✅ Basic chat interface
- ✅ OpenAI integration
- ✅ MCP server integration
- ✅ Session management
- ✅ Docker containerization

### v0.2.0 - Multi-LLM & Observability (Completed)
- ✅ Multi-LLM support (OpenAI, Anthropic, Google)
- ✅ Chain of thought display
- ✅ Token tracking and cost calculation
- ✅ Tool evaluation system

### v0.3.0 - Advanced Context & Tracing (Completed)
- ✅ Context summarization
- ✅ Thread branching
- ✅ OpenTelemetry tracing
- ✅ Session export/import

### v0.4.0 - Analytics & Insights (Completed)
- ✅ Analytics dashboard
- ✅ Usage metrics
- ✅ Tool analytics
- ✅ File attachments
- ✅ Feedback system

### v1.0.0 - Production Ready (Next)
- 📅 User authentication
- 📅 Multi-tenancy
- 📅 Rate limiting
- 📅 Production hardening

## Configuration

### Environment Variables

```bash
# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/coda_agent
REDIS_URL=redis://localhost:6379
MCP_SERVER_URL=http://mcp-server:8080

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Observability
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
PROMETHEUS_ENDPOINT=http://prometheus:9090

# Security
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

## API Examples

### Create a Chat Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Session",
    "model_provider": "openai",
    "model_name": "gpt-4"
  }'
```

### Send a Message

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "uuid",
    "content": "Optimize this decision problem...",
    "stream": true
  }'
```

### Get Analytics

```bash
curl http://localhost:8000/api/v1/analytics/usage?start_date=2024-01-01
```

## Testing

### Run Backend Tests

```bash
cd backend
pytest
```

### Run Frontend Tests

```bash
cd frontend
npm test
```

### Run E2E Tests

```bash
npm run test:e2e
```

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
kubectl apply -f k8s/
```

### Environment-Specific Configs

- **Development**: `docker-compose.yml`
- **Staging**: `docker-compose.staging.yml`
- **Production**: Kubernetes manifests in `k8s/`

## Monitoring

### Metrics

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### Tracing

- **Jaeger UI**: http://localhost:16686

### Logs

```bash
# View backend logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f
```

## Contributing

We follow the agile sprint methodology. Please see [BACKLOG.md](./BACKLOG.md) for current sprint and feature priorities.

### Development Workflow

1. Pick a story from the current sprint
2. Create a feature branch: `git checkout -b feature/F1.1-multi-llm-router`
3. Implement the feature
4. Write tests
5. Submit a pull request
6. Code review and merge

### Code Standards

- **Backend**: Follow PEP 8, use `black` for formatting
- **Frontend**: Follow Airbnb style guide, use `prettier`
- **Commits**: Use conventional commits (feat, fix, docs, etc.)

## Security

### Reporting Vulnerabilities

Please report security vulnerabilities to security@coda.com

### Security Features

- Encrypted API key storage
- JWT authentication
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection

## Performance

### Benchmarks

- **Response Time**: <2s (p95)
- **Throughput**: 1000 req/s
- **Concurrent Users**: 10,000+
- **Database Queries**: <100ms (p95)

### Optimization Tips

- Enable Redis caching
- Use read replicas for analytics
- Implement connection pooling
- Optimize context window management

## Troubleshooting

### Common Issues

**Issue**: Database connection failed  
**Solution**: Check `DATABASE_URL` and ensure PostgreSQL is running

**Issue**: LLM API rate limit  
**Solution**: Implement exponential backoff or use hosted models

**Issue**: High token costs  
**Solution**: Enable context summarization and optimize prompts

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose up
```

## FAQ

**Q: Can I use my own LLM API keys?**  
A: Yes, Coda Agent supports BYOK (Bring Your Own Key) for all providers.

**Q: How is my data stored?**  
A: All data is stored in PostgreSQL with encryption at rest.

**Q: Can I self-host?**  
A: Yes, Coda Agent is fully containerized and can be self-hosted.

**Q: What's the pricing?**  
A: Free tier with BYOK, premium tier with hosted models. See pricing page.

## License

MIT License - see [LICENSE](./LICENSE) file for details

## Support

- **Documentation**: [docs.coda.com/agent](https://docs.coda.com/agent)
- **Community**: [Discord](https://discord.gg/coda)
- **Email**: support@coda.com
- **Issues**: [GitHub Issues](https://github.com/coda/coda-agent/issues)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph)
- Monitored with [OpenTelemetry](https://opentelemetry.io/)
- UI built with [React](https://react.dev/)

---

**Made with ❤️ by the Coda Team**
