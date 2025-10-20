"""
Database layer using TinyDB for persistence
"""
from tinydb import TinyDB, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os


class Database:
    """Database manager for MCP server"""
    
    def __init__(self, db_path: str = "./data/mcp_db.json"):
        """Initialize database"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db = TinyDB(db_path)
        self.prompts = self.db.table('prompts')
        self.resources = self.db.table('resources')
        self.tools = self.db.table('tools')
        self.query = Query()
    
    # ===== Prompts =====
    
    def create_prompt(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prompt"""
        prompt_id = f"prompt_{uuid.uuid4().hex[:8]}"
        prompt = {
            "id": prompt_id,
            **data,
            "updated_at": datetime.now().isoformat()
        }
        self.prompts.insert(prompt)
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a prompt by ID"""
        result = self.prompts.search(self.query.id == prompt_id)
        return result[0] if result else None
    
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts"""
        return self.prompts.all()
    
    def update_prompt(self, prompt_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a prompt"""
        existing = self.get_prompt(prompt_id)
        if not existing:
            return None
        
        # Filter out None values
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        self.prompts.update(update_data, self.query.id == prompt_id)
        return self.get_prompt(prompt_id)
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt"""
        result = self.prompts.remove(self.query.id == prompt_id)
        return len(result) > 0
    
    # ===== Resources =====
    
    def create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource"""
        resource_id = f"resource_{uuid.uuid4().hex[:8]}"
        resource = {
            "id": resource_id,
            **data,
            "updated_at": datetime.now().isoformat()
        }
        self.resources.insert(resource)
        return resource
    
    def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get a resource by ID"""
        result = self.resources.search(self.query.id == resource_id)
        return result[0] if result else None
    
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Get all resources"""
        return self.resources.all()
    
    def update_resource(self, resource_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a resource"""
        existing = self.get_resource(resource_id)
        if not existing:
            return None
        
        # Filter out None values
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        self.resources.update(update_data, self.query.id == resource_id)
        return self.get_resource(resource_id)
    
    def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource"""
        result = self.resources.remove(self.query.id == resource_id)
        return len(result) > 0
    
    # ===== Tools =====
    
    def create_tool(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tool"""
        tool_id = f"tool_{uuid.uuid4().hex[:8]}"
        tool = {
            "id": tool_id,
            **data,
            "updated_at": datetime.now().isoformat()
        }
        self.tools.insert(tool)
        return tool
    
    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a tool by ID"""
        result = self.tools.search(self.query.id == tool_id)
        return result[0] if result else None
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools"""
        return self.tools.all()
    
    def update_tool(self, tool_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a tool"""
        existing = self.get_tool(tool_id)
        if not existing:
            return None
        
        # Filter out None values
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        self.tools.update(update_data, self.query.id == tool_id)
        return self.get_tool(tool_id)
    
    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool"""
        result = self.tools.remove(self.query.id == tool_id)
        return len(result) > 0
    
    def clear_all(self):
        """Clear all data (for testing)"""
        self.prompts.truncate()
        self.resources.truncate()
        self.tools.truncate()

