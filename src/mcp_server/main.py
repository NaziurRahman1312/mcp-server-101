"""
MCP Server - Hybrid approach using MCP SDK types + FastAPI
 
Why not FastMCP?
- FastMCP is designed for stdio/SSE transport with its own server runtime
- Cursor expects HTTP with JSON-RPC 2.0 at POST /
- This hybrid approach: uses MCP SDK types for validation + manual JSON-RPC handling
- This is the correct pattern for HTTP-based MCP servers with FastAPI
"""
from typing import List, Any, Dict
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
            
            result = {
                "description": f"{prompt.get('role', '')} prompt",
                "messages": [{
                    "role": prompt.get('role', 'user'),
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
