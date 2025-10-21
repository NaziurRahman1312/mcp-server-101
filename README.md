# MCP Server

A production-ready HTTP-based MCP (Model Context Protocol) server for managing prompts, resources, and tools. Built with the **official MCP Python SDK**, FastAPI, TinyDB, and Python 3.12.

## 🚀 Features

- ✅ **Official MCP SDK** - Type-safe protocol implementation
- ✅ **CRUD Operations** - Full REST API for managing data
- ✅ **JSON-RPC 2.0** - Standard MCP protocol support
- ✅ **Cursor Integration** - Ready for IDE integration
- ✅ **Persistent Storage** - TinyDB JSON database
- ✅ **Auto Documentation** - Swagger UI at `/docs`

## 📋 Prerequisites

- Python 3.12+
- pip

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd /Users/mdnaziurrahman/Documents/mcp-server-101
python3.12 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### 2. Seed the Database

```bash
python scripts/seed_data.py
```

This creates sample data:
- 4 Prompts (Code Review, Documentation, Bug Analysis, API Design)
- 4 Resources (RabbitMQ, Python Async, FastAPI, Git Workflow)
- 4 Tools (DB Backup, Log Analyzer, API Health Check, Docker Cleanup)

### 3. Start the Server

```bash
python run_server.py
```

Server starts at: **http://127.0.0.1:8000**

## 📁 Project Structure

```
mcp-server-101/
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       ├── main.py           # FastAPI app with MCP protocol
│       ├── models.py          # Pydantic data models
│       └── database.py        # TinyDB persistence layer
├── scripts/
│   └── seed_data.py          # Database seeding script
├── tests/                    # Test directory (future)
├── docs/                     # Documentation (future)
├── data/                     # Database storage (auto-created)
│   └── mcp_db.json
├── venv/                     # Virtual environment
├── run_server.py            # Server entry point
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md               # This file
```

## 🔌 API Endpoints

### MCP Protocol (JSON-RPC 2.0)

**Endpoint:** `POST /`

Supported methods:
- `initialize` - Initialize MCP connection
- `notifications/initialized` - Client notification
- `resources/list` - List all resources
- `resources/read` - Read resource content
- `prompts/list` - List all prompts
- `prompts/get` - Get specific prompt
- `tools/list` - List all tools
- `tools/call` - Execute a tool
- `ping` - Health check

### CRUD API

**Prompts:**
- `GET /prompts` - List all
- `GET /prompts/{id}` - Get one
- `POST /prompts` - Create
- `PUT /prompts/{id}` - Update
- `DELETE /prompts/{id}` - Delete

**Resources:**
- `GET /resources` - List all
- `GET /resources/{id}` - Get one
- `POST /resources` - Create
- `PUT /resources/{id}` - Update
- `DELETE /resources/{id}` - Delete

**Tools:**
- `GET /tools` - List all
- `GET /tools/{id}` - Get one
- `POST /tools` - Create
- `PUT /tools/{id}` - Update
- `DELETE /tools/{id}` - Delete

### Management API Endpoints

**Statistics & Analytics:**
- `GET /api/stats` - Get comprehensive statistics

**Search & Filter:**
- `GET /api/search?q={query}&type={type}` - Universal search
- `GET /api/prompts/filter?role={role}&tag={tag}` - Filter prompts
- `GET /api/resources/filter?category={category}` - Filter resources
- `GET /api/tools/filter?tag={tag}` - Filter tools

**Bulk Operations:**
- `POST /api/prompts/bulk` - Create multiple prompts
- `POST /api/resources/bulk` - Create multiple resources
- `POST /api/tools/bulk` - Create multiple tools
- `DELETE /api/prompts/bulk` - Delete multiple prompts
- `DELETE /api/resources/bulk` - Delete multiple resources
- `DELETE /api/tools/bulk` - Delete multiple tools

**Export & Import:**
- `GET /api/export` - Export all data as JSON
- `POST /api/import?mode={merge|replace}` - Import data from JSON

**Tags & Categories:**
- `GET /api/tags` - Get all unique tags
- `GET /api/categories` - Get all unique categories

### Utility Endpoints

- `GET /` - Server info
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation

## 🔍 Using with Cursor

### 1. Configure Cursor

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

### 2. Restart Cursor

Your MCP server will appear as "dev-mcp" with access to all your prompts, resources, and tools.

## 🧪 Testing

### Quick Demo

Try the interactive demo to see all management features:

```bash
python scripts/demo_management_api.py
```

This demo showcases:
- Statistics and analytics
- Search functionality
- Filtering capabilities
- Bulk operations
- Data export/import
- Tag management

### Test with cURL

```bash
# Initialize MCP
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# List resources
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}'

# CRUD - Get all resources
curl http://localhost:8000/resources

# CRUD - Create a prompt
curl -X POST http://localhost:8000/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Prompt",
    "role": "system",
    "content": "You are a helpful assistant",
    "tags": ["custom"]
  }'

# Management - Get statistics
curl http://localhost:8000/api/stats

# Management - Search for items
curl "http://localhost:8000/api/search?q=rabbitmq"

# Management - Filter prompts by role
curl "http://localhost:8000/api/prompts/filter?role=system"

# Management - Export data
curl http://localhost:8000/api/export > backup.json

# Management - Get all tags
curl http://localhost:8000/api/tags
```

**📚 Full API Documentation:** See [docs/MANAGEMENT_API.md](docs/MANAGEMENT_API.md) for complete management API documentation with examples.

## 📊 Data Models

### Prompt

```python
{
  "id": "prompt_abc123",
  "name": "Code Review Assistant",
  "role": "system",  # system | user | assistant
  "content": "You are a code reviewer...",
  "tags": ["code-review"],
  "updated_at": "2025-10-20T10:00:00"
}
```

### Resource

```python
{
  "id": "resource_abc123",
  "name": "RabbitMQ Guide",
  "description": "Complete RabbitMQ setup guide",
  "content": "# RabbitMQ...",
  "category": "Messaging",
  "updated_at": "2025-10-20T10:00:00"
}
```

### Tool

```python
{
  "id": "tool_abc123",
  "name": "Database Backup",
  "description": "Backup script for PostgreSQL",
  "code": "#!/bin/bash...",
  "tags": ["database", "backup"],
  "updated_at": "2025-10-20T10:00:00"
}
```

## 🔧 Development

### Running Tests

```bash
# TODO: Add tests
pytest tests/
```

### Re-seeding Database

```bash
python scripts/seed_data.py
```

### Adding New Data

Use the CRUD API or add directly to `scripts/seed_data.py`

## 🐛 Troubleshooting

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Import errors:**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**Database issues:**
```bash
# Reset with fresh seed data
python scripts/seed_data.py
```

## 📦 Dependencies

Core:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `mcp[cli]` - **Official MCP SDK**
- `tinydb` - JSON database

See `requirements.txt` for complete list.

## 🎓 Next Steps (Roadmap)

### Phase 2: FAISS Integration
- Add vector embeddings
- Semantic search capability
- Find by meaning, not keywords

### Phase 3: Meta Tool Endpoints
- Auto-generate from code
- Let Cursor build knowledge base
- Self-growing documentation

### Phase 4: Advanced Features
- Version history
- Team collaboration
- Multi-modal resources

## 📝 Notes

- Server runs on localhost only by default (127.0.0.1)
- Database persists between server restarts
- All data stored in `data/mcp_db.json`
- Hot reload enabled for development

## 📄 License

MIT License - Feel free to use and modify as needed.

## 🤝 Contributing

This is a personal/learning project. Feel free to fork and customize!

---

**Built with ❤️ using the official MCP Python SDK**
