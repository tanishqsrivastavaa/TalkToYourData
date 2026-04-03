# TalkToYourData

Voice-native Agentic RAG system - Talk to your documents using AI-powered voice conversations.

## Features

- 🎤 **Voice Conversations**: Natural voice interactions with your documents
- 📄 **Document Upload**: Support for PDF, Markdown, and text files
- 🔍 **RAG (Retrieval-Augmented Generation)**: Semantic search using pgvector
- 🤖 **AI Agent**: Powered by OpenAI GPT-4o-mini and Whisper
- 🔊 **Ultra-low Latency TTS**: Cartesia Sonic-3 for natural voice responses
- 🔐 **Authentication**: JWT-based user authentication
- 🎯 **Real-time**: WebRTC via LiveKit for reliable voice communication

## Tech Stack

- **Backend**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL 16 with pgvector extension
- **Caching**: Redis
- **Voice Infrastructure**: LiveKit
- **AI Models**: 
  - STT: OpenAI Whisper
  - LLM: OpenAI GPT-4o-mini
  - TTS: Cartesia Sonic-3
  - Embeddings: OpenAI text-embedding-3-small
- **ORM**: SQLModel (async)

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Docker & Docker Compose
- OpenAI API key
- Cartesia API key (get one at https://cartesia.ai)

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd TalkToYourData

# Install dependencies
pip install uv  # Modern Python package manager
uv sync

# Or use pip
pip install -e .
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# - OPENAI_API_KEY
# - CARTESIA_API_KEY
```

### 4. Start Services

```bash
# Start all services (database, redis, livekit, api, agent)
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Try the Voice Demo

```bash
# Open demo.html in your browser
open demo.html

# Or access via file://path/to/demo.html
```

**Demo Flow:**
1. Login with demo@example.com / password123 (or register new account)
2. Upload documents via the API (see below)
3. Click "Connect to Voice Agent"
4. Start talking about your documents!

## API Usage

### Register/Login

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

### Upload Documents

```bash
# Upload a PDF
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/document.pdf"

# List documents
curl http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Start Voice Conversation

1. Get LiveKit token:
```bash
curl -X POST http://localhost:8000/api/v1/livekit/token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"room_name": "my-room"}'
```

2. Use the token to connect via the demo frontend or your own client

## Documentation

- **[VOICE_AGENT.md](./VOICE_AGENT.md)**: Detailed voice agent setup and configuration guide
- **API Docs**: http://localhost:8000/docs (when running)

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌───────────────┐
│   Browser   │ ◄─────► │ LiveKit      │ ◄─────► │ Agent Worker  │
│   (WebRTC)  │         │ Server       │         │ (STT/LLM/TTS) │
└─────────────┘         └──────────────┘         └───────┬───────┘
                                                          │
      │                                                   │
      │                                                   ▼
      │                                          ┌────────────────┐
      └─────────────────────────────────────────►│ FastAPI Backend│
                    REST API                     │ (Auth, Docs)   │
                                                 └────────┬───────┘
                                                          │
                                                          ▼
                                                 ┌────────────────┐
                                                 │  PostgreSQL    │
                                                 │  + pgvector    │
                                                 └────────────────┘
```

## How It Works

1. **User uploads documents** → Parsed, chunked, and embedded
2. **User authenticates** → Gets JWT token
3. **User requests LiveKit token** → Joins voice room
4. **Agent joins room** → Starts listening
5. **User speaks** → Whisper transcribes → RAG retrieves context → GPT generates response → Cartesia speaks
6. **Real-time conversation** with document-aware responses

## Development

### Running Locally (without Docker)

```bash
# Terminal 1: Start infrastructure
docker-compose up db redis livekit

# Terminal 2: Start API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Start agent worker
python agent_worker.py
```

### Run Tests

```bash
pytest
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Troubleshooting

See [VOICE_AGENT.md](./VOICE_AGENT.md) for detailed troubleshooting guide.

**Common Issues:**
- **Agent doesn't join**: Check agent worker logs, verify LiveKit is running
- **No audio**: Check browser microphone permissions, audio output not muted
- **RAG not working**: Ensure embeddings are generated (check document_chunks table)

## Production Deployment

See [VOICE_AGENT.md](./VOICE_AGENT.md) for production considerations including:
- Embedding generation optimization
- Scalability (multiple agent workers)
- Security hardening
- Monitoring and observability
- Cost optimization

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
