# Coda Agent - Technical Specification

## System Architecture

### Overview
Coda Agent is a microservices-based application containerized with Docker, consisting of:
- **Frontend**: React SPA served by Nginx
- **Backend**: FastAPI application server
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis for session management
- **Observability**: Prometheus, Grafana, Jaeger

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                            │
│                         (Nginx/Traefik)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐       ┌───────▼────────┐
        │   Frontend     │       │    Backend     │
        │   (Nginx)      │       │   (FastAPI)    │
        │   React SPA    │       │   Python 3.11  │
        └────────────────┘       └───────┬────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
            ┌───────▼────────┐  ┌────────▼───────┐  ┌────────▼────────┐
            │   PostgreSQL   │  │     Redis      │  │ Cloud Run APIs   │
            │   (Primary)    │  │   (Cache)      │  │ (Via Bridge)     │
            └────────────────┘  └────────────────┘  └─────────────────┘
                    │
            ┌───────▼────────┐
            │   PostgreSQL   │
            │   (Replica)    │
            └────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Observability Stack                           │
├─────────────────────────────────────────────────────────────────┤
│  Prometheus  │  Grafana  │  Jaeger  │  OpenTelemetry Collector │
└─────────────────────────────────────────────────────────────────┘
```

**Architecture Update (v0.1.0)**: Use of "Virtual MCP Bridge" pattern where the Backend directly bridges LLM calls to Tool APIs without a separate MCP Server container.

---

## Data Models

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    organization_id UUID REFERENCES organizations(id),
    api_keys JSONB DEFAULT '{}',  -- Encrypted API keys
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Organizations Table
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',  -- free, pro, enterprise
    quota_tokens INTEGER DEFAULT 100000,
    quota_requests INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Sessions Table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    model_provider VARCHAR(50),  -- openai, anthropic, google, hosted
    model_name VARCHAR(100),
    system_prompt TEXT,
    context_summary TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
```

#### Messages Table
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

#### Tool Calls Table
```sql
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    input_params JSONB NOT NULL,
    output_result JSONB,
    status VARCHAR(50),  -- pending, success, error
    error_message TEXT,
    execution_time_ms INTEGER,
    evaluation JSONB,  -- Quality scores, appropriateness, etc.
    trace_id VARCHAR(255),  -- OpenTelemetry trace ID
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tool_calls_session_id ON tool_calls(session_id);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);
CREATE INDEX idx_tool_calls_created_at ON tool_calls(created_at);
```

#### Chain of Thought Table
```sql
CREATE TABLE chain_of_thought (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_type VARCHAR(50),  -- reasoning, tool_selection, parameter_eval, etc.
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cot_message_id ON chain_of_thought(message_id);
```

#### Analytics Events Table
```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    properties JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
```

#### Embeddings Table (for semantic search)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE message_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_message_embeddings_vector ON message_embeddings 
USING ivfflat (embedding vector_cosine_ops);
```

---

## API Specification

### REST API Endpoints

#### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

#### Sessions
```
GET    /api/v1/sessions
POST   /api/v1/sessions
GET    /api/v1/sessions/{session_id}
PATCH  /api/v1/sessions/{session_id}
DELETE /api/v1/sessions/{session_id}
POST   /api/v1/sessions/{session_id}/export
POST   /api/v1/sessions/import
```

#### Messages
```
GET    /api/v1/sessions/{session_id}/messages
POST   /api/v1/sessions/{session_id}/messages
GET    /api/v1/messages/{message_id}
POST   /api/v1/messages/{message_id}/branch
```

#### Chat (Streaming)
```
POST   /api/v1/chat/stream  (Server-Sent Events)
```

#### Tools
```
GET    /api/v1/tools
GET    /api/v1/tools/{tool_name}
POST   /api/v1/tools/{tool_name}/execute
```

#### Analytics
```
GET    /api/v1/analytics/usage
GET    /api/v1/analytics/tools
GET    /api/v1/analytics/decisions
GET    /api/v1/analytics/export
```

#### Settings
```
GET    /api/v1/settings
PATCH  /api/v1/settings
POST   /api/v1/settings/api-keys
DELETE /api/v1/settings/api-keys/{provider}
```

### WebSocket API

#### Real-time Chat
```
WS /api/v1/ws/chat/{session_id}

Client -> Server:
{
  "type": "message",
  "content": "User message",
  "model": "gpt-4"
}

Server -> Client:
{
  "type": "message_start",
  "message_id": "uuid"
}
{
  "type": "content_delta",
  "delta": "chunk of text"
}
{
  "type": "tool_call",
  "tool_name": "solver_optimize",
  "input": {...}
}
{
  "type": "tool_result",
  "tool_name": "solver_optimize",
  "output": {...}
}
{
  "type": "message_end",
  "tokens": {"input": 100, "output": 200},
  "processing_time_ms": 1500
}
```

---

## Backend Architecture

### Directory Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── sessions.py
│   │   │   ├── messages.py
│   │   │   ├── chat.py
│   │   │   ├── tools.py
│   │   │   ├── analytics.py
│   │   │   └── settings.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── tool_call.py
│   │   └── analytics.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── tool.py
│   │   └── analytics.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Abstract LLM interface
│   │   │   ├── openai.py
│   │   │   ├── anthropic.py
│   │   │   ├── google.py
│   │   │   └── router.py       # LLM router
│   │   │
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py # Main agent loop
│   │   │   ├── context.py      # Context management
│   │   │   ├── memory.py       # Memory management
│   │   │   └── evaluator.py    # Tool/answer evaluation
│   │   │
│   │   ├── mcp/
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # MCP API client
│   │   │   ├── schema.py       # Schema parser
│   │   │   └── registry.py     # Tool registry
│   │   │
│   │   ├── tracing/
│   │   │   ├── __init__.py
│   │   │   ├── otel.py         # OpenTelemetry setup
│   │   │   └── middleware.py   # Tracing middleware
│   │   │
│   │   └── analytics/
│   │       ├── __init__.py
│   │       ├── collector.py    # Event collection
│   │       └── aggregator.py   # Data aggregation
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py          # Database session
│   │   ├── migrations/         # Alembic migrations
│   │   └── repositories/       # Data access layer
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── session.py
│   │       ├── message.py
│   │       └── tool_call.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Auth, encryption
│   │   ├── cache.py            # Redis cache
│   │   └── exceptions.py       # Custom exceptions
│   │
│   └── utils/
│       ├── __init__.py
│       ├── token_counter.py
│       ├── cost_calculator.py
│       └── validators.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── alembic.ini
├── pyproject.toml
├── poetry.lock
└── Dockerfile
```

### Key Components

#### LLM Router (`services/llm/router.py`)
```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List

class BaseLLM(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        stream: bool = False
    ) -> AsyncIterator[Dict]:
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass

class LLMRouter:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "google": GoogleProvider(),
            "hosted": HostedProvider()
        }
    
    def get_provider(self, provider_name: str, api_key: str = None) -> BaseLLM:
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        if api_key:
            provider.set_api_key(api_key)
        
        return provider
```

#### Agent Orchestrator (`services/agent/orchestrator.py`)
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict

class AgentState(TypedDict):
    messages: List[Dict]
    tools: List[Dict]
    tool_calls: List[Dict]
    context: str
    next_action: str

class AgentOrchestrator:
    def __init__(self, llm: BaseLLM, mcp_client: MCPClient):
        self.llm = llm
        self.mcp_client = mcp_client
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        workflow.add_node("reason", self._reason_step)
        workflow.add_node("select_tool", self._select_tool_step)
        workflow.add_node("execute_tool", self._execute_tool_step)
        workflow.add_node("synthesize", self._synthesize_step)
        
        workflow.add_edge("reason", "select_tool")
        workflow.add_conditional_edges(
            "select_tool",
            self._should_use_tool,
            {
                "use_tool": "execute_tool",
                "no_tool": "synthesize"
            }
        )
        workflow.add_edge("execute_tool", "reason")
        workflow.add_edge("synthesize", END)
        
        workflow.set_entry_point("reason")
        
        return workflow.compile()
    
    async def run(self, user_message: str, context: Dict) -> AsyncIterator[Dict]:
        state = {
            "messages": [{"role": "user", "content": user_message}],
            "tools": await self.mcp_client.get_tools(),
            "tool_calls": [],
            "context": context.get("summary", ""),
            "next_action": "reason"
        }
        
        async for event in self.graph.astream(state):
            yield event
```

#### MCP Virtual Bridge (`services/tools_bridge.py`)
```python
import httpx
from typing import List, Dict

class ToolsBridge:
    def __init__(self):
        # Scans local tools/ directory for schema.json files
        self.tools_registry = self._load_tools()
    
    def get_openai_tools(self) -> List[Dict]:
        """Convert loaded schemas to OpenAI 'functions' format"""
        # ... transformation logic
        return openai_tools_list
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict
    ) -> Dict:
        """Execute a tool via direct HTTP call to Cloud Run URL defined in schema"""
        url = self.tools_registry[tool_name]["url"]
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=parameters)
            return resp.json()
```

---

## Frontend Architecture

### Directory Structure
```
frontend/
├── public/
│   ├── index.html
│   └── assets/
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   │
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageItem.tsx
│   │   │   ├── InputBox.tsx
│   │   │   ├── ToolCallDisplay.tsx
│   │   │   └── StreamingMessage.tsx
│   │   │
│   │   ├── session/
│   │   │   ├── SessionList.tsx
│   │   │   ├── SessionItem.tsx
│   │   │   └── NewSessionButton.tsx
│   │   │
│   │   ├── cot/
│   │   │   ├── ChainOfThoughtPanel.tsx
│   │   │   ├── ReasoningStep.tsx
│   │   │   └── ToolEvaluation.tsx
│   │   │
│   │   ├── analytics/
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   ├── UsageChart.tsx
│   │   │   ├── ToolChart.tsx
│   │   │   └── DecisionChart.tsx
│   │   │
│   │   ├── settings/
│   │   │   ├── SettingsPanel.tsx
│   │   │   ├── ModelSelector.tsx
│   │   │   ├── APIKeyManager.tsx
│   │   │   └── PreferencesForm.tsx
│   │   │
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Modal.tsx
│   │       └── Spinner.tsx
│   │
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useSession.ts
│   │   ├── useWebSocket.ts
│   │   ├── useAnalytics.ts
│   │   └── useSettings.ts
│   │
│   ├── store/
│   │   ├── index.ts
│   │   ├── chatStore.ts
│   │   ├── sessionStore.ts
│   │   ├── settingsStore.ts
│   │   └── analyticsStore.ts
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   ├── sessions.ts
│   │   ├── messages.ts
│   │   ├── tools.ts
│   │   └── analytics.ts
│   │
│   ├── types/
│   │   ├── chat.ts
│   │   ├── session.ts
│   │   ├── tool.ts
│   │   └── analytics.ts
│   │
│   └── utils/
│       ├── formatters.ts
│       ├── validators.ts
│       └── constants.ts
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

### Key Components

#### Chat Interface (`components/chat/ChatInterface.tsx`)
```typescript
import { useChat } from '@/hooks/useChat';
import { MessageList } from './MessageList';
import { InputBox } from './InputBox';
import { ChainOfThoughtPanel } from '@/components/cot/ChainOfThoughtPanel';

export function ChatInterface({ sessionId }: { sessionId: string }) {
  const {
    messages,
    isStreaming,
    sendMessage,
    currentCoT,
    metrics
  } = useChat(sessionId);

  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col">
        <MessageList messages={messages} isStreaming={isStreaming} />
        <InputBox onSend={sendMessage} disabled={isStreaming} />
        
        {/* Metrics Bar */}
        <div className="p-2 bg-gray-100 text-sm flex gap-4">
          <span>Tokens: {metrics.tokens}</span>
          <span>Cost: ${metrics.cost.toFixed(4)}</span>
          <span>Time: {metrics.time}ms</span>
        </div>
      </div>
      
      {/* Chain of Thought Panel */}
      <ChainOfThoughtPanel steps={currentCoT} />
    </div>
  );
}
```

#### WebSocket Hook (`hooks/useWebSocket.ts`)
```typescript
import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url: string) {
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => setIsConnected(true);
    ws.current.onclose = () => setIsConnected(false);
    ws.current.onmessage = (event) => {
      setLastMessage(JSON.parse(event.data));
    };

    return () => {
      ws.current?.close();
    };
  }, [url]);

  const sendMessage = (message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { isConnected, lastMessage, sendMessage };
}
```

---

## Deployment

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://backend:8000

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://coda:password@postgres:5432/coda_agent
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MCP_SERVER_URL=${MCP_SERVER_URL}
    volumes:
      - ./backend:/app

  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=coda
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=coda_agent
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./observability/grafana/dashboards:/etc/grafana/provisioning/dashboards

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

## Security Considerations

### API Key Storage
- Encrypt API keys using Fernet (symmetric encryption)
- Store encryption key in environment variable
- Never log API keys

### Authentication
- JWT tokens with short expiration (15 min)
- Refresh tokens with longer expiration (7 days)
- HTTP-only cookies for web clients

### Rate Limiting
- Per-user rate limits
- Per-organization quotas
- Token-based throttling

### Input Validation
- Pydantic schema validation
- SQL injection prevention (parameterized queries)
- XSS prevention (sanitize outputs)

---

## Performance Optimization

### Caching Strategy
- Redis for session data (TTL: 1 hour)
- Tool schema caching (TTL: 24 hours)
- User preferences caching

### Database Optimization
- Indexes on frequently queried columns
- Connection pooling
- Read replicas for analytics queries

### Frontend Optimization
- Code splitting
- Lazy loading components
- Virtual scrolling for long message lists
- Debounced input

---

## Monitoring & Alerting

### Key Metrics
- Request latency (p50, p95, p99)
- Error rate
- Token usage per user
- Tool execution time
- Database query time

### Alerts
- Error rate > 1%
- Latency p95 > 3s
- Database connection pool exhausted
- Redis connection failures
- LLM API failures

---

## Testing Strategy

### Unit Tests
- Service layer logic
- Utility functions
- Schema validation

### Integration Tests
- API endpoints
- Database operations
- LLM provider integrations

### E2E Tests
- Complete chat flows
- Tool calling scenarios
- Session management

### Load Tests
- 1000 concurrent users
- 10,000 messages/minute
- Tool execution under load

---

## Migration Strategy

### Phase 1: Development
- Local Docker Compose setup
- SQLite for rapid iteration
- Mock MCP server

### Phase 2: Staging
- Cloud deployment (AWS/Azure)
- PostgreSQL database
- Real MCP server integration

### Phase 3: Production
- Multi-region deployment
- Database replication
- CDN for frontend
- Auto-scaling

