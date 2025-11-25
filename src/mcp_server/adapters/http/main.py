"""
FastAPI application exposing both CRUD and MCP JSON-RPC interfaces.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp.types import Prompt as MCPPrompt
from mcp.types import Resource as MCPResource
from mcp.types import TextContent, Tool as MCPTool
from pydantic import ValidationError
from sqlalchemy.orm import Session

from mcp_server.adapters.http import schemas
from mcp_server.core.config import get_settings
from mcp_server.domain import models
from mcp_server.infrastructure.db.sqlite import Base, engine, session_scope
from mcp_server.infrastructure.repositories.sqlite_repo import (
    PromptSQLiteRepository,
    ResourceSQLiteRepository,
    ToolSQLiteRepository,
)
from mcp_server.infrastructure.vector.faiss_store import FaissStore
from mcp_server.usecases.prompt_service import PromptService
from mcp_server.usecases.resource_service import ResourceService
from mcp_server.usecases.search_service import SearchService
from mcp_server.usecases.tool_service import ToolService

settings = get_settings()
vector_store = FaissStore()
MetaHandler = Callable[[Dict[str, Any]], str]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart MCP Server",
        version="2.0.0",
        description="Clean architecture MCP server with FAISS-powered semantic search.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    register_routes(app)
    return app



def get_session() -> Iterable[Session]:
    with session_scope() as session:
        yield session


def get_prompt_service(session: Session = Depends(get_session)) -> PromptService:
    return PromptService(PromptSQLiteRepository(session))


def get_resource_service(session: Session = Depends(get_session)) -> ResourceService:
    return ResourceService(ResourceSQLiteRepository(session), vector_store)


def get_tool_service(session: Session = Depends(get_session)) -> ToolService:
    return ToolService(ToolSQLiteRepository(session), vector_store)


def get_search_service(
    session: Session = Depends(get_session),
) -> SearchService:
    return SearchService(
        prompts=PromptSQLiteRepository(session),
        resources=ResourceSQLiteRepository(session),
        tools=ToolSQLiteRepository(session),
        vector_store=vector_store,
    )


def register_routes(app: FastAPI) -> None:
    api = APIRouter(prefix="/api/v1")

    # ----- Prompts -----
    @api.get("/prompts", response_model=List[schemas.PromptResponse])
    def list_prompts(service: PromptService = Depends(get_prompt_service)):
        return [schemas.PromptResponse.from_domain(p) for p in service.list_prompts()]

    @api.get("/prompts/{prompt_id}", response_model=schemas.PromptResponse)
    def get_prompt(prompt_id: str, service: PromptService = Depends(get_prompt_service)):
        prompt = service.get_prompt(prompt_id)
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        return schemas.PromptResponse.from_domain(prompt)

    @api.post("/prompts", response_model=schemas.PromptResponse, status_code=status.HTTP_201_CREATED)
    def create_prompt(payload: models.PromptCreate, service: PromptService = Depends(get_prompt_service)):
        prompt = service.create_prompt(payload)
        return schemas.PromptResponse.from_domain(prompt)

    @api.put("/prompts/{prompt_id}", response_model=schemas.PromptResponse)
    def update_prompt(prompt_id: str, payload: models.PromptUpdate, service: PromptService = Depends(get_prompt_service)):
        prompt = service.update_prompt(prompt_id, payload)
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        return schemas.PromptResponse.from_domain(prompt)

    @api.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_prompt(prompt_id: str, service: PromptService = Depends(get_prompt_service)):
        if not service.delete_prompt(prompt_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    # ----- Resources -----
    @api.get("/resources", response_model=List[schemas.ResourceResponse])
    def list_resources(service: ResourceService = Depends(get_resource_service)):
        return [schemas.ResourceResponse.from_domain(r) for r in service.list_resources()]

    @api.get("/resources/{resource_id}", response_model=schemas.ResourceResponse)
    def get_resource(resource_id: str, service: ResourceService = Depends(get_resource_service)):
        resource = service.get_resource(resource_id)
        if not resource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        return schemas.ResourceResponse.from_domain(resource)

    @api.post("/resources", response_model=schemas.ResourceResponse, status_code=status.HTTP_201_CREATED)
    def create_resource(payload: models.ResourceCreate, service: ResourceService = Depends(get_resource_service)):
        resource = service.create_resource(payload)
        return schemas.ResourceResponse.from_domain(resource)

    @api.put("/resources/{resource_id}", response_model=schemas.ResourceResponse)
    def update_resource(
        resource_id: str,
        payload: models.ResourceUpdate,
        service: ResourceService = Depends(get_resource_service),
    ):
        resource = service.update_resource(resource_id, payload)
        if not resource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        return schemas.ResourceResponse.from_domain(resource)

    @api.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_resource(resource_id: str, service: ResourceService = Depends(get_resource_service)):
        if not service.delete_resource(resource_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    # ----- Tools -----
    @api.get("/tools", response_model=List[schemas.ToolResponse])
    def list_tools(service: ToolService = Depends(get_tool_service)):
        return [schemas.ToolResponse.from_domain(t) for t in service.list_tools()]

    @api.get("/tools/{tool_id}", response_model=schemas.ToolResponse)
    def get_tool(tool_id: str, service: ToolService = Depends(get_tool_service)):
        tool = service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        return schemas.ToolResponse.from_domain(tool)

    @api.post("/tools", response_model=schemas.ToolResponse, status_code=status.HTTP_201_CREATED)
    def create_tool(payload: models.ToolCreate, service: ToolService = Depends(get_tool_service)):
        tool = service.create_tool(payload)
        return schemas.ToolResponse.from_domain(tool)

    @api.put("/tools/{tool_id}", response_model=schemas.ToolResponse)
    def update_tool(
        tool_id: str,
        payload: models.ToolUpdate,
        service: ToolService = Depends(get_tool_service),
    ):
        tool = service.update_tool(tool_id, payload)
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        return schemas.ToolResponse.from_domain(tool)

    @api.delete("/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_tool(tool_id: str, service: ToolService = Depends(get_tool_service)):
        if not service.delete_tool(tool_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

    # ----- Search -----
    @api.get("/search")
    def search(
        q: str,
        target: Literal["prompt", "resource", "tool", "all"] = "all",
        service: SearchService = Depends(get_search_service),
    ):
        actual_target = None if target == "all" else target  # type: ignore[assignment]
        hits = service.search(q, target=actual_target, limit=settings.faiss_top_k)
        return {
            "query": q,
            "results": [
                schemas.SearchResultResponse(
                    id=hit.id,
                    type=hit.type,
                    score=hit.score,
                    payload=_to_schema(hit.payload),
                )
                for hit in hits
            ],
        }

    app.include_router(api)

    # ----- Informational endpoints -----
    @app.get("/")
    def root():
        return {
            "name": settings.app_name,
            "protocol": "mcp",
            "version": "2024-11-05",
            "capabilities": {"prompts": True, "resources": True, "tools": True},
            "endpoints": {
                "json_rpc": "/",
                "api": "/api/v1",
                "health": "/health",
            },
        }

    @app.get("/health")
    def health():
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

    @app.post("/")
    async def mcp_rpc(request: Request, search_service: SearchService = Depends(get_search_service)):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(status_code=400, content=jsonrpc_error(None, -32700, "Parse error"))

        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"resources": {}, "prompts": {}, "tools": {}},
                    "serverInfo": {"name": settings.app_name, "version": "2.0.0"},
                }
                return JSONResponse(content=jsonrpc_response(req_id, result))
            if method == "notifications/initialized":
                return JSONResponse(content={"jsonrpc": "2.0"})
            if method == "resources/list":
                resources = search_service.resources.list()
                payload = [
                    MCPResource(
                        uri=f"resource:///{r.id}",
                        name=r.name,
                        description=r.description,
                        mimeType="text/markdown",
                    ).model_dump(mode="json")
                    for r in resources
                ]
                return JSONResponse(content=jsonrpc_response(req_id, {"resources": payload}))
            if method == "resources/read":
                uri = params.get("uri", "")
                resource_id = uri.replace("resource:///", "")
                resource = search_service.resources.get(resource_id)
                if not resource:
                    return JSONResponse(
                        status_code=404,
                        content=jsonrpc_error(req_id, -32602, f"Resource not found: {resource_id}"),
                    )
                result = {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/markdown",
                            "text": resource.content,
                        }
                    ]
                }
                return JSONResponse(content=jsonrpc_response(req_id, result))
            if method == "prompts/list":
                prompts = search_service.prompts.list()
                payload = [
                    MCPPrompt(name=p.name, description=p.content[:80], arguments=[]).model_dump(mode="json")
                    for p in prompts
                ]
                return JSONResponse(content=jsonrpc_response(req_id, {"prompts": payload}))
            if method == "prompts/get":
                prompt_name = params.get("name")
                prompt = next((p for p in search_service.prompts.list() if p.name == prompt_name), None)
                if not prompt:
                    return JSONResponse(
                        status_code=404,
                        content=jsonrpc_error(req_id, -32602, f"Prompt not found: {prompt_name}"),
                    )
                role = "user" if prompt.role in (models.PromptRole.system, models.PromptRole.user) else "assistant"
                return JSONResponse(
                    content=jsonrpc_response(
                        req_id,
                        {
                            "description": prompt.content[:120],
                            "messages": [
                                {
                                    "role": role,
                                    "content": {"type": "text", "text": prompt.content},
                                }
                            ],
                        },
                    )
                )
            if method == "tools/list":
                stored_tools = search_service.tools.list()
                meta_payload = [
                    MCPTool(
                        name=tool["name"],
                        description=tool["description"],
                        inputSchema=tool["schema"],
                    ).model_dump(mode="json")
                    for tool in META_TOOL_DEFINITIONS
                ]
                stored_payload = [
                    MCPTool(
                        name=t.name,
                        description=t.description,
                        inputSchema={"type": "object", "properties": {}},
                    ).model_dump(mode="json")
                    for t in stored_tools
                ]
                payload = meta_payload + stored_payload
                return JSONResponse(content=jsonrpc_response(req_id, {"tools": payload}))
            if method == "tools/call":
                tool_name = params.get("name")
                meta_tool = META_TOOL_MAP.get(tool_name)
                if meta_tool:
                    try:
                        text_result = meta_tool["handler"](params.get("arguments") or {})
                    except ValueError as exc:
                        return JSONResponse(
                            status_code=400,
                            content=jsonrpc_error(req_id, -32602, str(exc)),
                        )
                    content = TextContent(type="text", text=text_result)
                    return JSONResponse(
                        content=jsonrpc_response(
                            req_id,
                            {"content": [content.model_dump(mode="json")], "isError": False},
                        )
                    )
                tool = next((t for t in search_service.tools.list() if t.name == tool_name), None)
                if not tool:
                    return JSONResponse(
                        status_code=404,
                        content=jsonrpc_error(req_id, -32602, f"Tool not found: {tool_name}"),
                    )
                content = TextContent(type="text", text=f"Tool '{tool.name}' code:\n\n```\n{tool.code}\n```")
                return JSONResponse(content=jsonrpc_response(req_id, {"content": [content.model_dump()], "isError": False}))
            if method == "ping":
                return JSONResponse(content=jsonrpc_response(req_id, {}))

            return JSONResponse(
                status_code=404,
                content=jsonrpc_error(req_id, -32601, f"Method not found: {method}"),
            )
        except Exception as exc:  # pragma: no cover - defensive
            return JSONResponse(
                status_code=500,
                content=jsonrpc_error(req_id, -32603, f"Internal error: {exc}"),
            )


def jsonrpc_response(req_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def jsonrpc_error(req_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _to_schema(obj: models.Prompt | models.Resource | models.Tool):
    if isinstance(obj, models.Prompt):
        return schemas.PromptResponse.from_domain(obj)
    if isinstance(obj, models.Resource):
        return schemas.ResourceResponse.from_domain(obj)
    return schemas.ToolResponse.from_domain(obj)


def _with_prompt_service_action(action: Callable[[PromptService], Any]) -> Any:
    with session_scope() as session:
        service = PromptService(PromptSQLiteRepository(session))
        return action(service)


def _with_resource_service_action(action: Callable[[ResourceService], Any]) -> Any:
    with session_scope() as session:
        service = ResourceService(ResourceSQLiteRepository(session), vector_store)
        return action(service)


def _with_tool_service_action(action: Callable[[ToolService], Any]) -> Any:
    with session_scope() as session:
        service = ToolService(ToolSQLiteRepository(session), vector_store)
        return action(service)


def _with_search_service_action(action: Callable[[SearchService], Any]) -> Any:
    with session_scope() as session:
        service = SearchService(
            prompts=PromptSQLiteRepository(session),
            resources=ResourceSQLiteRepository(session),
            tools=ToolSQLiteRepository(session),
            vector_store=vector_store,
        )
        return action(service)


def _json_text(data: Any) -> str:
    return json.dumps(data, indent=2)


def _extract_update_fields(args: Dict[str, Any], allowed: List[str]) -> Dict[str, Any]:
    payload = {field: args[field] for field in allowed if field in args and args[field] is not None}
    if not payload:
        raise ValueError("Provide at least one field to update.")
    return payload


def _meta_create_prompt(args: Dict[str, Any]) -> str:
    try:
        payload = models.PromptCreate(**args)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    prompt = _with_prompt_service_action(lambda svc: svc.create_prompt(payload))
    return _json_text({"prompt": schemas.PromptResponse.from_domain(prompt).model_dump(mode="json")})


def _meta_update_prompt(args: Dict[str, Any]) -> str:
    prompt_id = args.get("id")
    if not prompt_id:
        raise ValueError("id is required")
    update_fields = _extract_update_fields(args, ["name", "role", "content", "tags"])
    try:
        payload = models.PromptUpdate(**update_fields)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    def _action(service: PromptService):
        updated = service.update_prompt(prompt_id, payload)
        if not updated:
            raise ValueError(f"Prompt not found: {prompt_id}")
        return updated

    prompt = _with_prompt_service_action(_action)
    return _json_text({"prompt": schemas.PromptResponse.from_domain(prompt).model_dump(mode="json")})


def _meta_create_resource(args: Dict[str, Any]) -> str:
    try:
        payload = models.ResourceCreate(**args)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    resource = _with_resource_service_action(lambda svc: svc.create_resource(payload))
    return _json_text({"resource": schemas.ResourceResponse.from_domain(resource).model_dump(mode="json")})


def _meta_update_resource(args: Dict[str, Any]) -> str:
    resource_id = args.get("id")
    if not resource_id:
        raise ValueError("id is required")
    update_fields = _extract_update_fields(args, ["name", "description", "content", "category", "tags"])
    try:
        payload = models.ResourceUpdate(**update_fields)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    def _action(service: ResourceService):
        updated = service.update_resource(resource_id, payload)
        if not updated:
            raise ValueError(f"Resource not found: {resource_id}")
        return updated

    resource = _with_resource_service_action(_action)
    return _json_text({"resource": schemas.ResourceResponse.from_domain(resource).model_dump(mode="json")})


def _meta_create_tool(args: Dict[str, Any]) -> str:
    try:
        payload = models.ToolCreate(**args)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    tool = _with_tool_service_action(lambda svc: svc.create_tool(payload))
    return _json_text({"tool": schemas.ToolResponse.from_domain(tool).model_dump(mode="json")})


def _meta_update_tool(args: Dict[str, Any]) -> str:
    tool_id = args.get("id")
    if not tool_id:
        raise ValueError("id is required")
    update_fields = _extract_update_fields(args, ["name", "description", "code", "tags"])
    try:
        payload = models.ToolUpdate(**update_fields)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    def _action(service: ToolService):
        updated = service.update_tool(tool_id, payload)
        if not updated:
            raise ValueError(f"Tool not found: {tool_id}")
        return updated

    tool = _with_tool_service_action(_action)
    return _json_text({"tool": schemas.ToolResponse.from_domain(tool).model_dump(mode="json")})


def _meta_search_resources(args: Dict[str, Any]) -> str:
    query = (args or {}).get("query")
    if not query:
        raise ValueError("query is required")
    results = _with_search_service_action(lambda svc: svc.search(query, target="resource", limit=settings.faiss_top_k))
    payload = {
        "query": query,
        "results": [
            {
                "score": hit.score,
                "resource": schemas.ResourceResponse.from_domain(hit.payload).model_dump(mode="json"),
            }
            for hit in results
        ],
    }
    return _json_text(payload)


def _meta_search_tools(args: Dict[str, Any]) -> str:
    query = (args or {}).get("query")
    if not query:
        raise ValueError("query is required")
    results = _with_search_service_action(lambda svc: svc.search(query, target="tool", limit=settings.faiss_top_k))
    payload = {
        "query": query,
        "results": [
            {
                "score": hit.score,
                "tool": schemas.ToolResponse.from_domain(hit.payload).model_dump(mode="json"),
            }
            for hit in results
        ],
    }
    return _json_text(payload)


PROMPT_ROLE_VALUES = [role.value for role in models.PromptRole]

META_TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "meta.createPrompt",
        "description": "Create a prompt without using the REST API.",
        "schema": {
            "type": "object",
            "required": ["name", "role", "content"],
            "properties": {
                "name": {"type": "string"},
                "role": {"type": "string", "enum": PROMPT_ROLE_VALUES},
                "content": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "handler": _meta_create_prompt,
    },
    {
        "name": "meta.updatePrompt",
        "description": "Update an existing prompt by ID.",
        "schema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "role": {"type": "string", "enum": PROMPT_ROLE_VALUES},
                "content": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "handler": _meta_update_prompt,
    },
    {
        "name": "meta.createResource",
        "description": "Create a resource via MCP meta tool.",
        "schema": {
            "type": "object",
            "required": ["name", "description", "content", "category"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "content": {"type": "string"},
                "category": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "handler": _meta_create_resource,
    },
    {
        "name": "meta.updateResource",
        "description": "Update a resource by ID.",
        "schema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "content": {"type": "string"},
                "category": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "handler": _meta_update_resource,
    },
    {
        "name": "meta.createTool",
        "description": "Create a tool record through MCP.",
        "schema": {
            "type": "object",
            "required": ["name", "description", "code"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "code": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "handler": _meta_create_tool,
    },
    {
        "name": "meta.updateTool",
        "description": "Update a stored tool by ID.",
        "schema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "code": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "handler": _meta_update_tool,
    },
    {
        "name": "meta.searchResources",
        "description": "Semantic search over resources using FAISS embeddings.",
        "schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
            },
        },
        "handler": _meta_search_resources,
    },
    {
        "name": "meta.searchTools",
        "description": "Semantic search over tools using FAISS embeddings.",
        "schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
            },
        },
        "handler": _meta_search_tools,
    },
]

META_TOOL_MAP: Dict[str, Dict[str, Any]] = {tool["name"]: tool for tool in META_TOOL_DEFINITIONS}



app = create_app()

