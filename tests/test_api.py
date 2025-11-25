from __future__ import annotations

import os
import shutil
import tempfile
import json
from importlib import reload
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# Configure test-specific storage before importing the app
TMP_DIR = Path(tempfile.mkdtemp(prefix="mcp-test-"))
ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))
os.environ["MCP_DATABASE_URL"] = f"sqlite:///{TMP_DIR / 'db.sqlite3'}"
os.environ["MCP_FAISS_INDEX_PATH"] = str(TMP_DIR / "faiss.index")

from mcp_server.core import config as config_module

config_module.get_settings.cache_clear()

from mcp_server.adapters.http import main as http_main
from mcp_server.infrastructure.db.sqlite import Base, engine
from mcp_server.infrastructure.vector.faiss_store import FaissStore

reload(http_main)


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(http_main.app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_state():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    index_path = Path(os.environ["MCP_FAISS_INDEX_PATH"])
    meta_path = index_path.with_suffix(".meta.json")
    for path in (index_path, meta_path):
        if path.exists():
            path.unlink()
    http_main.vector_store = FaissStore()
    yield


def test_prompt_crud_flow(client: TestClient):
    payload = {
        "name": "pytest prompt",
        "role": "system",
        "content": "Respond in JSON.",
        "tags": ["pytest"],
    }
    create_resp = client.post("/api/v1/prompts", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()

    get_resp = client.get(f"/api/v1/prompts/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == payload["name"]

    update_resp = client.put(
        f"/api/v1/prompts/{created['id']}",
        json={"content": "Updated content."},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["content"] == "Updated content."

    delete_resp = client.delete(f"/api/v1/prompts/{created['id']}")
    assert delete_resp.status_code == 204

    missing = client.get(f"/api/v1/prompts/{created['id']}")
    assert missing.status_code == 404


def test_semantic_search_returns_results(client: TestClient):
    resource_payload = {
        "name": "Vector Databases Overview",
        "description": "Comparing FAISS and other ANN libraries.",
        "content": "FAISS is a library for efficient similarity search in high dimensional spaces.",
        "category": "AI",
    }
    tool_payload = {
        "name": "Backup Script",
        "description": "Creates a tarball backup.",
        "code": "tar -czf backup.tar.gz ./data",
        "tags": ["backup"],
    }
    client.post("/api/v1/resources", json=resource_payload)
    client.post("/api/v1/tools", json=tool_payload)

    resp = client.get("/api/v1/search", params={"q": "similarity search"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"], "expected semantic hits for seeded data"
    types = {hit["type"] for hit in body["results"]}
    assert {"resource", "tool"} & types


def _rpc_call(client: TestClient, method: str, params: Dict[str, Any] | None = None, request_id: int = 1) -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
    resp = client.post("/", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "error" not in body, body
    return body


def _call_meta_tool(client: TestClient, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    body = _rpc_call(client, "tools/call", {"name": name, "arguments": arguments})
    result = body["result"]
    assert not result.get("isError", False)
    return result


def test_meta_tools_create_update_and_search(client: TestClient):
    resource_args = {
        "name": "Vector Knowledge Base",
        "description": "Internal KB for similarity search instructions.",
        "content": "Always use FAISS for semantic lookups.",
        "category": "Knowledge",
        "tags": ["kb", "vector"],
    }
    create_resource_result = _call_meta_tool(client, "meta.createResource", resource_args)
    created_payload = json.loads(create_resource_result["content"][0]["text"])
    resource_id = created_payload["resource"]["id"]

    tool_args = {
        "name": "Embedding Refresher",
        "description": "Rebuilds FAISS index.",
        "code": "python scripts/reindex.py",
        "tags": ["faiss", "ops"],
    }
    _call_meta_tool(client, "meta.createTool", tool_args)

    _call_meta_tool(client, "meta.updateResource", {"id": resource_id, "category": "Playbooks"})

    resources = client.get("/api/v1/resources").json()
    assert any(r["id"] == resource_id and r["category"] == "Playbooks" for r in resources)

    search_resources = _call_meta_tool(client, "meta.searchResources", {"query": "semantic lookups"})
    resource_hits = json.loads(search_resources["content"][0]["text"])["results"]
    assert resource_hits

    search_tools = _call_meta_tool(client, "meta.searchTools", {"query": "FAISS index"})
    tool_hits = json.loads(search_tools["content"][0]["text"])["results"]
    assert any(hit["tool"]["name"] == tool_args["name"] for hit in tool_hits)


def test_meta_tools_listed(client: TestClient):
    body = _rpc_call(client, "tools/list")
    names = {tool["name"] for tool in body["result"]["tools"]}
    assert "meta.createResource" in names
    assert "meta.searchTools" in names


def teardown_module(module):
    shutil.rmtree(TMP_DIR, ignore_errors=True)


