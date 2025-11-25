"""
MCP Server - Entry point
Run this file to start the server
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from mcp_server.main import app
import uvicorn

if __name__ == "__main__":
    print("\n🚀 MCP Server Starting...")
    print("=" * 60)
    print("📡 MCP Protocol: JSON-RPC 2.0 at POST /")
    print("🔧 Management API: http://127.0.0.1:8000/api/v1")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("❤️  Health: http://127.0.0.1:8000/health")
    print("=" * 60)
    print("✅ FAISS-backed semantic search for resources/tools")
    print("✅ Ready for Cursor integration\n")
    
    uvicorn.run(
        "mcp_server.adapters.http.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir=str(src_path)
    )

