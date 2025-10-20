"""
MCP Server - Hybrid approach using MCP SDK types + FastAPI
 
Why not FastMCP?
- FastMCP is designed for stdio/SSE transport with its own server runtime
- Cursor expects HTTP with JSON-RPC 2.0 at POST /
- This hybrid approach: uses MCP SDK types for validation + manual JSON-RPC handling
- This is the correct pattern for HTTP-based MCP servers with FastAPI
"""
from typing import List, Any, Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, status as http_status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# MCP SDK imports - using types for validation, not FastMCP
from mcp.types import Resource, Tool, Prompt, TextContent

# Local imports
from mcp_server.models import (
    Prompt as PromptModel, PromptCreate, PromptUpdate,
    Resource as ResourceModel, ResourceCreate, ResourceUpdate,
    Tool as ToolModel, ToolCreate, ToolUpdate,
    MCPResponse
)
from mcp_server.database import Database

# Initialize database
db = Database()

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server",
    description="HTTP-based MCP server with JSON-RPC 2.0 protocol (using MCP SDK types)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== JSON-RPC 2.0 Helper Functions =====

def jsonrpc_response(id: Any, result: Any) -> Dict:
    """Create JSON-RPC 2.0 success response"""
    return {"jsonrpc": "2.0", "id": id, "result": result}


def jsonrpc_error(id: Any, code: int, message: str) -> Dict:
    """Create JSON-RPC 2.0 error response"""
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message}
    }


# ===== MCP Protocol Handler (JSON-RPC 2.0) =====

@app.post("/")
async def mcp_json_rpc_handler(request: Request):
    """
    Main MCP JSON-RPC 2.0 endpoint
    Uses MCP SDK types (Resource, Tool, Prompt, TextContent) for validation
    
    Note: We handle JSON-RPC manually because Fast MCP is designed for stdio/SSE,
    not HTTP JSON-RPC which Cursor expects.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            content=jsonrpc_error(None, -32700, "Parse error"),
            status_code=400
        )
    
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")
    
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "resources": {},
                    "prompts": {},
                    "tools": {}
                },
                "serverInfo": {
                    "name": "dev-mcp",
                    "version": "1.0.0"
                }
            }
            return JSONResponse(content=jsonrpc_response(req_id, result))
        
        elif method == "notifications/initialized":
            return JSONResponse(content={"jsonrpc": "2.0"})
        
        elif method == "resources/list":
            resources = db.get_all_resources()
            # Use MCP SDK Resource type for validation
            mcp_resources = [
                Resource(
                    uri=f"resource:///{r['id']}",
                    name=r['name'],
                    description=r.get('description', ''),
                    mimeType="text/markdown"
                )
                for r in resources
            ]
            result = {"resources": [r.model_dump(mode='json') for r in mcp_resources]}
            return JSONResponse(content=jsonrpc_response(req_id, result))
        
        elif method == "resources/read":
            uri = params.get("uri", "")
            resource_id = uri.replace("resource:///", "")
            resource = db.get_resource(resource_id)
            
            if not resource:
                return JSONResponse(
                    content=jsonrpc_error(req_id, -32602, f"Resource not found: {resource_id}"),
                    status_code=404
                )
            
            result = {
                "contents": [{
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": resource['content']
                }]
            }
            return JSONResponse(content=jsonrpc_response(req_id, result))
        
        elif method == "prompts/list":
            prompts = db.get_all_prompts()
            # Use MCP SDK Prompt type for validation
            mcp_prompts = [
                Prompt(
                    name=p['name'],
                    description=p.get('content', '')[:100] + "..." if len(p.get('content', '')) > 100 else p.get('content', ''),
                    arguments=[]
                )
                for p in prompts
            ]
            result = {"prompts": [p.model_dump(mode='json') for p in mcp_prompts]}
            return JSONResponse(content=jsonrpc_response(req_id, result))
        
        elif method == "prompts/get":
            prompt_name = params.get("name", "")
            prompts = db.get_all_prompts()
            prompt = next((p for p in prompts if p['name'] == prompt_name), None)
            
            if not prompt:
                return JSONResponse(
                    content=jsonrpc_error(req_id, -32602, f"Prompt not found: {prompt_name}"),
                    status_code=404
                )
            
            # Map stored role to valid MCP message role (only 'user' or 'assistant' allowed)
            stored_role = prompt.get('role', 'user')
            mcp_role = 'user' if stored_role in ['user', 'system'] else 'assistant'
            
            result = {
                "description": prompt.get('description', f"{stored_role} prompt"),
                "messages": [{
                    "role": mcp_role,
                    "content": {
                        "type": "text",
                        "text": prompt['content']
                    }
                }]
            }
            return JSONResponse(content=jsonrpc_response(req_id, result))
        
        elif method == "tools/list":
            tools = db.get_all_tools()
            # Use MCP SDK Tool type for validation
            mcp_tools = [
                Tool(
                    name=t['name'],
                    description=t.get('description', ''),
                    inputSchema={"type": "object", "properties": {}}
                )
                for t in tools
            ]
            result = {"tools": [t.model_dump(mode='json') for t in mcp_tools]}
            return JSONResponse(content=jsonrpc_response(req_id, result))
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tools = db.get_all_tools()
            tool = next((t for t in tools if t['name'] == tool_name), None)
            
            if not tool:
                return JSONResponse(
                    content=jsonrpc_error(req_id, -32602, f"Tool not found: {tool_name}"),
                    status_code=404
                )
            
            # Use MCP SDK TextContent type
            content = TextContent(
                type="text",
                text=f"Tool '{tool_name}' code:\n\n```\n{tool['code']}\n```"
            )
            result = {
                "content": [content.model_dump(mode='json')],
                "isError": False
            }
            return JSONResponse(content=jsonrpc_response(req_id, result))
        
        elif method == "ping":
            return JSONResponse(content=jsonrpc_response(req_id, {}))
        
        else:
            return JSONResponse(
                content=jsonrpc_error(req_id, -32601, f"Method not found: {method}"),
                status_code=404
            )
    
    except Exception as e:
        return JSONResponse(
            content=jsonrpc_error(req_id, -32603, f"Internal error: {str(e)}"),
            status_code=500
        )


# ===== Info Endpoints =====

@app.get("/")
def root_info():
    """Root endpoint - server info (GET for browser access)"""
    return {
        "protocol": "mcp",
        "version": "2024-11-05",
        "transport": "HTTP with JSON-RPC 2.0",
        "implementation": "Hybrid: MCP SDK types + Manual JSON-RPC (correct for HTTP)",
        "why_not_fastmcp": "FastMCP is for stdio/SSE, Cursor needs HTTP JSON-RPC",
        "server": {
            "name": "dev-mcp",
            "description": "Local MCP server for prompts, tools, and resources"
        },
        "capabilities": {
            "prompts": True,
            "resources": True,
            "tools": True
        },
        "available_methods": [
            "initialize",
            "resources/list",
            "resources/read",
            "prompts/list",
            "prompts/get",
            "tools/list",
            "tools/call",
            "ping"
        ],
        "crud_endpoints": {
            "prompts": "/prompts",
            "resources": "/resources",
            "tools": "/tools"
        },
        "management_endpoints": {
            "statistics": "/api/stats",
            "search": "/api/search?q={query}&type={prompt|resource|tool}",
            "filters": {
                "prompts": "/api/prompts/filter?role={role}&tag={tag}",
                "resources": "/api/resources/filter?category={category}",
                "tools": "/api/tools/filter?tag={tag}"
            },
            "bulk_operations": {
                "create": "/api/{type}/bulk (POST)",
                "delete": "/api/{type}/bulk (DELETE)"
            },
            "export": "/api/export",
            "import": "/api/import?mode={merge|replace}",
            "tags": "/api/tags",
            "categories": "/api/categories"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ===== Prompts CRUD Endpoints =====

@app.get("/prompts", response_model=List[PromptModel])
def get_prompts():
    """Get all prompts"""
    return db.get_all_prompts()


@app.get("/prompts/{prompt_id}", response_model=PromptModel)
def get_prompt_by_id(prompt_id: str):
    """Get a specific prompt by ID"""
    prompt = db.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@app.post("/prompts", response_model=PromptModel, status_code=http_status.HTTP_201_CREATED)
def create_prompt(prompt: PromptCreate):
    """Create a new prompt"""
    prompt_data = prompt.model_dump()
    new_prompt = db.create_prompt(prompt_data)
    return new_prompt


@app.put("/prompts/{prompt_id}", response_model=PromptModel)
def update_prompt(prompt_id: str, prompt: PromptUpdate):
    """Update an existing prompt"""
    prompt_data = prompt.model_dump(exclude_none=True)
    updated_prompt = db.update_prompt(prompt_id, prompt_data)
    if not updated_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return updated_prompt


@app.delete("/prompts/{prompt_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: str):
    """Delete a prompt"""
    success = db.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")


# ===== Resources CRUD Endpoints =====

@app.get("/resources", response_model=List[ResourceModel])
def get_resources():
    """Get all resources"""
    return db.get_all_resources()


@app.get("/resources/{resource_id}", response_model=ResourceModel)
def get_resource_by_id(resource_id: str):
    """Get a specific resource by ID"""
    resource = db.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@app.post("/resources", response_model=ResourceModel, status_code=http_status.HTTP_201_CREATED)
def create_resource(resource: ResourceCreate):
    """Create a new resource"""
    resource_data = resource.model_dump()
    new_resource = db.create_resource(resource_data)
    return new_resource


@app.put("/resources/{resource_id}", response_model=ResourceModel)
def update_resource(resource_id: str, resource: ResourceUpdate):
    """Update an existing resource"""
    resource_data = resource.model_dump(exclude_none=True)
    updated_resource = db.update_resource(resource_id, resource_data)
    if not updated_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return updated_resource


@app.delete("/resources/{resource_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_resource(resource_id: str):
    """Delete a resource"""
    success = db.delete_resource(resource_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resource not found")


# ===== Tools CRUD Endpoints =====

@app.get("/tools", response_model=List[ToolModel])
def get_tools():
    """Get all tools"""
    return db.get_all_tools()


@app.get("/tools/{tool_id}", response_model=ToolModel)
def get_tool_by_id(tool_id: str):
    """Get a specific tool by ID"""
    tool = db.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@app.post("/tools", response_model=ToolModel, status_code=http_status.HTTP_201_CREATED)
def create_tool(tool: ToolCreate):
    """Create a new tool"""
    tool_data = tool.model_dump()
    new_tool = db.create_tool(tool_data)
    return new_tool


@app.put("/tools/{tool_id}", response_model=ToolModel)
def update_tool(tool_id: str, tool: ToolUpdate):
    """Update an existing tool"""
    tool_data = tool.model_dump(exclude_none=True)
    updated_tool = db.update_tool(tool_id, tool_data)
    if not updated_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return updated_tool


@app.delete("/tools/{tool_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_tool(tool_id: str):
    """Delete a tool"""
    success = db.delete_tool(tool_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")


# ===== Enhanced Management Endpoints =====

# --- Statistics & Analytics ---

@app.get("/api/stats")
def get_statistics():
    """Get overall statistics about prompts, resources, and tools"""
    prompts = db.get_all_prompts()
    resources = db.get_all_resources()
    tools = db.get_all_tools()
    
    # Collect tag statistics
    prompt_tags = {}
    for p in prompts:
        for tag in p.get('tags', []):
            prompt_tags[tag] = prompt_tags.get(tag, 0) + 1
    
    tool_tags = {}
    for t in tools:
        for tag in t.get('tags', []):
            tool_tags[tag] = tool_tags.get(tag, 0) + 1
    
    # Collect role statistics for prompts
    role_stats = {}
    for p in prompts:
        role = p.get('role', 'unknown')
        role_stats[role] = role_stats.get(role, 0) + 1
    
    # Collect category statistics for resources
    category_stats = {}
    for r in resources:
        cat = r.get('category', 'uncategorized')
        category_stats[cat] = category_stats.get(cat, 0) + 1
    
    return {
        "summary": {
            "total_prompts": len(prompts),
            "total_resources": len(resources),
            "total_tools": len(tools),
            "total_items": len(prompts) + len(resources) + len(tools)
        },
        "prompts": {
            "count": len(prompts),
            "by_role": role_stats,
            "top_tags": dict(sorted(prompt_tags.items(), key=lambda x: x[1], reverse=True)[:10])
        },
        "resources": {
            "count": len(resources),
            "by_category": category_stats
        },
        "tools": {
            "count": len(tools),
            "top_tags": dict(sorted(tool_tags.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    }


# --- Search & Filter Endpoints ---

@app.get("/api/search")
def search_all(q: str, type: Optional[str] = None):
    """
    Search across all prompts, resources, and tools
    
    Query params:
    - q: search query (searches in name, content, description)
    - type: optional filter by type (prompt, resource, tool)
    """
    results = {"prompts": [], "resources": [], "tools": []}
    query_lower = q.lower()
    
    if not type or type == "prompt":
        prompts = db.get_all_prompts()
        results["prompts"] = [
            p for p in prompts 
            if query_lower in p.get('name', '').lower() 
            or query_lower in p.get('content', '').lower()
            or any(query_lower in tag.lower() for tag in p.get('tags', []))
        ]
    
    if not type or type == "resource":
        resources = db.get_all_resources()
        results["resources"] = [
            r for r in resources 
            if query_lower in r.get('name', '').lower() 
            or query_lower in r.get('description', '').lower()
            or query_lower in r.get('content', '').lower()
            or query_lower in r.get('category', '').lower()
        ]
    
    if not type or type == "tool":
        tools = db.get_all_tools()
        results["tools"] = [
            t for t in tools 
            if query_lower in t.get('name', '').lower() 
            or query_lower in t.get('description', '').lower()
            or query_lower in t.get('code', '').lower()
            or any(query_lower in tag.lower() for tag in t.get('tags', []))
        ]
    
    total = len(results["prompts"]) + len(results["resources"]) + len(results["tools"])
    
    return {
        "query": q,
        "total_results": total,
        "results": results
    }


@app.get("/api/prompts/filter")
def filter_prompts(role: Optional[str] = None, tag: Optional[str] = None):
    """Filter prompts by role and/or tag"""
    prompts = db.get_all_prompts()
    
    if role:
        prompts = [p for p in prompts if p.get('role') == role]
    
    if tag:
        prompts = [p for p in prompts if tag in p.get('tags', [])]
    
    return {
        "count": len(prompts),
        "filters": {"role": role, "tag": tag},
        "prompts": prompts
    }


@app.get("/api/resources/filter")
def filter_resources(category: Optional[str] = None):
    """Filter resources by category"""
    resources = db.get_all_resources()
    
    if category:
        resources = [r for r in resources if r.get('category') == category]
    
    return {
        "count": len(resources),
        "filters": {"category": category},
        "resources": resources
    }


@app.get("/api/tools/filter")
def filter_tools(tag: Optional[str] = None):
    """Filter tools by tag"""
    tools = db.get_all_tools()
    
    if tag:
        tools = [t for t in tools if tag in t.get('tags', [])]
    
    return {
        "count": len(tools),
        "filters": {"tag": tag},
        "tools": tools
    }


# --- Bulk Operations ---

@app.post("/api/prompts/bulk", status_code=http_status.HTTP_201_CREATED)
def create_prompts_bulk(prompts: List[PromptCreate]):
    """Create multiple prompts at once"""
    created = []
    for prompt in prompts:
        prompt_data = prompt.model_dump()
        new_prompt = db.create_prompt(prompt_data)
        created.append(new_prompt)
    
    return {
        "success": True,
        "count": len(created),
        "prompts": created
    }


@app.post("/api/resources/bulk", status_code=http_status.HTTP_201_CREATED)
def create_resources_bulk(resources: List[ResourceCreate]):
    """Create multiple resources at once"""
    created = []
    for resource in resources:
        resource_data = resource.model_dump()
        new_resource = db.create_resource(resource_data)
        created.append(new_resource)
    
    return {
        "success": True,
        "count": len(created),
        "resources": created
    }


@app.post("/api/tools/bulk", status_code=http_status.HTTP_201_CREATED)
def create_tools_bulk(tools: List[ToolCreate]):
    """Create multiple tools at once"""
    created = []
    for tool in tools:
        tool_data = tool.model_dump()
        new_tool = db.create_tool(tool_data)
        created.append(new_tool)
    
    return {
        "success": True,
        "count": len(created),
        "tools": created
    }


@app.delete("/api/prompts/bulk", status_code=http_status.HTTP_200_OK)
def delete_prompts_bulk(ids: List[str]):
    """Delete multiple prompts at once"""
    deleted = []
    failed = []
    
    for prompt_id in ids:
        success = db.delete_prompt(prompt_id)
        if success:
            deleted.append(prompt_id)
        else:
            failed.append(prompt_id)
    
    return {
        "success": len(failed) == 0,
        "deleted": deleted,
        "failed": failed,
        "deleted_count": len(deleted),
        "failed_count": len(failed)
    }


@app.delete("/api/resources/bulk", status_code=http_status.HTTP_200_OK)
def delete_resources_bulk(ids: List[str]):
    """Delete multiple resources at once"""
    deleted = []
    failed = []
    
    for resource_id in ids:
        success = db.delete_resource(resource_id)
        if success:
            deleted.append(resource_id)
        else:
            failed.append(resource_id)
    
    return {
        "success": len(failed) == 0,
        "deleted": deleted,
        "failed": failed,
        "deleted_count": len(deleted),
        "failed_count": len(failed)
    }


@app.delete("/api/tools/bulk", status_code=http_status.HTTP_200_OK)
def delete_tools_bulk(ids: List[str]):
    """Delete multiple tools at once"""
    deleted = []
    failed = []
    
    for tool_id in ids:
        success = db.delete_tool(tool_id)
        if success:
            deleted.append(tool_id)
        else:
            failed.append(tool_id)
    
    return {
        "success": len(failed) == 0,
        "deleted": deleted,
        "failed": failed,
        "deleted_count": len(deleted),
        "failed_count": len(failed)
    }


# --- Export & Import ---

@app.get("/api/export")
def export_all_data():
    """Export all data (prompts, resources, tools) as JSON"""
    return {
        "export_date": datetime.now().isoformat(),
        "data": {
            "prompts": db.get_all_prompts(),
            "resources": db.get_all_resources(),
            "tools": db.get_all_tools()
        }
    }


@app.post("/api/import", status_code=http_status.HTTP_201_CREATED)
def import_data(
    data: Dict[str, List[Dict[str, Any]]],
    mode: str = "merge"  # merge or replace
):
    """
    Import data from exported JSON
    
    Modes:
    - merge: Add new items alongside existing ones
    - replace: Clear existing data and import fresh
    """
    if mode == "replace":
        db.clear_all()
    
    stats = {
        "prompts_imported": 0,
        "resources_imported": 0,
        "tools_imported": 0
    }
    
    # Import prompts
    for prompt_data in data.get("prompts", []):
        # Remove id to generate new ones in merge mode
        if mode == "merge" and 'id' in prompt_data:
            del prompt_data['id']
        
        if mode == "replace":
            db.prompts.insert(prompt_data)
        else:
            # Validate against model first
            try:
                validated = PromptCreate(**prompt_data)
                db.create_prompt(validated.model_dump())
            except Exception:
                continue
        
        stats["prompts_imported"] += 1
    
    # Import resources
    for resource_data in data.get("resources", []):
        if mode == "merge" and 'id' in resource_data:
            del resource_data['id']
        
        if mode == "replace":
            db.resources.insert(resource_data)
        else:
            try:
                validated = ResourceCreate(**resource_data)
                db.create_resource(validated.model_dump())
            except Exception:
                continue
        
        stats["resources_imported"] += 1
    
    # Import tools
    for tool_data in data.get("tools", []):
        if mode == "merge" and 'id' in tool_data:
            del tool_data['id']
        
        if mode == "replace":
            db.tools.insert(tool_data)
        else:
            try:
                validated = ToolCreate(**tool_data)
                db.create_tool(validated.model_dump())
            except Exception:
                continue
        
        stats["tools_imported"] += 1
    
    return {
        "success": True,
        "mode": mode,
        "stats": stats
    }


# --- Tags & Categories Management ---

@app.get("/api/tags")
def get_all_tags():
    """Get all unique tags from prompts and tools"""
    prompts = db.get_all_prompts()
    tools = db.get_all_tools()
    
    prompt_tags = set()
    for p in prompts:
        prompt_tags.update(p.get('tags', []))
    
    tool_tags = set()
    for t in tools:
        tool_tags.update(t.get('tags', []))
    
    return {
        "prompt_tags": sorted(list(prompt_tags)),
        "tool_tags": sorted(list(tool_tags)),
        "all_tags": sorted(list(prompt_tags | tool_tags))
    }


@app.get("/api/categories")
def get_all_categories():
    """Get all unique categories from resources"""
    resources = db.get_all_resources()
    categories = set()
    
    for r in resources:
        categories.add(r.get('category', 'uncategorized'))
    
    return {
        "categories": sorted(list(categories)),
        "count": len(categories)
    }


# ===== Legacy MCP Endpoints (Backward Compatibility) =====

@app.post("/mcp/prompts/query", response_model=MCPResponse)
def mcp_query_prompts():
    """Legacy MCP endpoint to query all prompts"""
    prompts = db.get_all_prompts()
    return MCPResponse(success=True, data=prompts, count=len(prompts))


@app.post("/mcp/resources/query", response_model=MCPResponse)
def mcp_query_resources():
    """Legacy MCP endpoint to query all resources"""
    resources = db.get_all_resources()
    return MCPResponse(success=True, data=resources, count=len(resources))


@app.post("/mcp/tools/query", response_model=MCPResponse)
def mcp_query_tools():
    """Legacy MCP endpoint to query all tools"""
    tools = db.get_all_tools()
    return MCPResponse(success=True, data=tools, count=len(tools))


# Note: Server is started via run_server.py in the project root
