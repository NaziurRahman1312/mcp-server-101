# Smart MCP Server

An HTTP-friendly Model Context Protocol (MCP) server that exposes JSON-RPC for MCP clients and a versioned REST API for managing prompts, resources, and tools. The implementation follows a clean architecture split between domain, use cases, infrastructure, and adapters. Persistence relies on SQLite via SQLAlchemy while semantic search is powered by FAISS + sentence-transformer embeddings. Everything is container/Kubernetes ready and ships with automated tests.

## 🚀 Highlights

- Clean architecture layout (domain/usecases/adapters/infrastructure)
- FastAPI app with manual JSON-RPC handler compatible with Cursor and other MCP clients
- SQLite persistence via SQLAlchemy + Pydantic domain models
- FAISS vector store for semantic search over resources/tools
- SentenceTransformer embeddings (configurable model)
- Kubernetes manifests with persistent storage for DB + FAISS index
- Demo script and pytest-based API coverage
- Auto docs available at `/docs`

## 📋 Prerequisites

- Python 3.12+
- pip

## 🛠️ Installation

```bash
cd /Users/mdnaziurrahman/Documents/mcp-server-101
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1. Seed the database

```bash
python scripts/seed_data.py
```

This resets the SQLite database + FAISS index and loads curated prompts/resources/tools.

### 2. Run the server

```bash
python run_server.py
```

Endpoints:

- JSON-RPC MCP endpoint: `POST http://127.0.0.1:8000/`
- REST API root: `http://127.0.0.1:8000/api/v1`
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## 📁 Project Structure

```
mcp-server-101/
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       ├── core/                # configuration helpers
│       ├── domain/              # domain models + repository interfaces
│       ├── usecases/            # application services
│       ├── infrastructure/      # SQLite + FAISS adapters
│       └── adapters/http/       # FastAPI app + schemas
├── scripts/
│   └── seed_data.py
├── deploy/                      # Kubernetes manifests
├── tests/                       # pytest API coverage
├── docs/
├── run_server.py
├── requirements.txt
└── README.md
```

## ⚙️ Configuration

Environment variables (defaults live in `core/config.py`):

| Variable | Description | Default |
| --- | --- | --- |
| `MCP_DATABASE_URL` | SQLAlchemy URL | `sqlite:///data/mcp.db` |
| `MCP_FAISS_INDEX_PATH` | Path to FAISS index file | `data/faiss.index` |
| `MCP_EMBEDDING_MODEL_NAME` | SentenceTransformer model | `sentence-transformers/all-MiniLM-L6-v2` |
| `MCP_EMBEDDING_DIM` | Embedding vector dimension | `384` |
| `MCP_FAISS_TOP_K` | Default semantic result count | `5` |

## 🔌 API Overview

### MCP JSON-RPC (`POST /`)

Supported methods: `initialize`, `notifications/initialized`, `resources/list`, `resources/read`, `prompts/list`, `prompts/get`, `tools/list`, `tools/call`, `ping`.

### REST Management API (`/api/v1`)

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/prompts` | List prompts |
| `GET` | `/prompts/{id}` | Fetch prompt |
| `POST` | `/prompts` | Create prompt |
| `PUT` | `/prompts/{id}` | Update prompt |
| `DELETE` | `/prompts/{id}` | Delete prompt |
| `GET/POST/PUT/DELETE` | `/resources`, `/tools` | Same semantics for resources and tools |
| `GET` | `/search?q=...&target=all|prompt|resource|tool` | Semantic search backed by FAISS |
| `GET` | `/health` | Health probe |
| `GET` | `/docs` | FastAPI swagger docs |

### Quick cURL snippets

```bash
# Create a prompt
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{"name":"My Prompt","role":"system","content":"Hi","tags":["demo"]}'

# Semantic search
curl "http://localhost:8000/api/v1/search?q=vector+database"

# MCP initialize
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

## 🧰 Built-in Meta MCP Tools

The MCP `tools/list` response always includes a set of meta tools so Cursor (or any MCP client) can manage data without bespoke REST calls:

- `meta.createPrompt` / `meta.updatePrompt`
- `meta.createResource` / `meta.updateResource`
- `meta.createTool` / `meta.updateTool`
- `meta.searchResources` / `meta.searchTools` (FAISS-powered semantic search)

Invoke them with the standard `tools/call` RPC and pass the documented JSON schema in `arguments`. Responses echo the affected object (or search hits) as formatted JSON.

## 🔍 Using with Cursor

Create or update `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dev-mcp": {
      "url": "http://localhost:8000",
      "type": "http",
      "enabled": true
    }
  }
}
```

Your MCP server will appear as `dev-mcp` with access to prompts/resources/tools plus semantic search.

## 🧪 Testing

```bash
pytest
```

### Interactive demo

```bash
python scripts/demo_management_api.py
```

The script exercises health checks, CRUD, semantic search, and JSON-RPC discovery flow.

## ☁️ Kubernetes Deployment

```bash
kubectl apply -f deploy/pvc.yaml
kubectl apply -f deploy/deployment.yaml
kubectl apply -f deploy/service.yaml
```

The deployment mounts a PVC at `/app/data` so both SQLite and FAISS indexes persist across pod restarts. Update the `image` tag to point at your published container.

## 📦 Dependencies

- `fastapi`, `uvicorn[standard]`
- `pydantic`, `pydantic-settings`
- `sqlalchemy`
- `sentence-transformers`, `faiss-cpu`
- `mcp[cli]`
- `pytest` for tests

See `requirements.txt` for the full list.

## 📄 License

MIT License - Feel free to use and modify as needed.

## 🤝 Contributing

This is a personal/learning project. Feel free to fork and customize!

---

Built with ❤️ using the official MCP Python SDK.

