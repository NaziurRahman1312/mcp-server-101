"""
Seed data script to populate the database with test data
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from mcp_server.database import Database
from datetime import datetime


def seed_database():
    """Populate database with seed data"""
    db = Database()
    
    # Clear existing data
    print("Clearing existing data...")
    db.clear_all()
    
    print("\n🌱 Seeding database with test data...\n")
    
    # ===== Seed Prompts =====
    print("📝 Creating prompts...")
    
    prompts = [
        {
            "name": "Code Review Assistant",
            "role": "system",
            "content": "You are a senior code reviewer. Analyze the provided code for:\n1. Best practices\n2. Potential bugs\n3. Performance issues\n4. Security vulnerabilities\n\nProvide constructive feedback with specific examples.",
            "tags": ["code-review", "quality"]
        },
        {
            "name": "Documentation Generator",
            "role": "system",
            "content": "You are a technical writer. Generate clear, concise documentation for code including:\n- Purpose and overview\n- Function/class descriptions\n- Parameter explanations\n- Usage examples\n- Edge cases",
            "tags": ["documentation", "technical-writing"]
        },
        {
            "name": "Bug Analyzer",
            "role": "user",
            "content": "I'm experiencing a bug where {describe_bug}. Here's the relevant code:\n\n{code_snippet}\n\nCan you help me identify the issue and suggest a fix?",
            "tags": ["debugging", "troubleshooting"]
        },
        {
            "name": "API Design Consultant",
            "role": "system",
            "content": "You are an API design expert. Review API endpoints for:\n- RESTful principles\n- Proper HTTP methods and status codes\n- Clear naming conventions\n- Versioning strategy\n- Error handling\n\nProvide recommendations for improvements.",
            "tags": ["api", "design", "rest"]
        }
    ]
    
    for prompt in prompts:
        created = db.create_prompt(prompt)
        print(f"  ✓ Created prompt: {created['name']} ({created['id']})")
    
    # ===== Seed Resources =====
    print("\n📚 Creating resources...")
    
    resources = [
        {
            "name": "RabbitMQ Quick Start Guide",
            "description": "Complete guide for setting up and using RabbitMQ in Python applications",
            "category": "Messaging",
            "content": """# RabbitMQ Quick Start Guide

## Installation

```bash
# Install RabbitMQ server
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Install Python client
pip install pika
```

## Basic Publisher

```python
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()

# Declare queue
channel.queue_declare(queue='hello')

# Publish message
channel.basic_publish(
    exchange='',
    routing_key='hello',
    body='Hello World!'
)

print(" [x] Sent 'Hello World!'")
connection.close()
```

## Basic Consumer

```python
import pika

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()
channel.queue_declare(queue='hello')

channel.basic_consume(
    queue='hello',
    auto_ack=True,
    on_message_callback=callback
)

print(' [*] Waiting for messages...')
channel.start_consuming()
```

## Best Practices

1. Always close connections properly
2. Use connection pooling for production
3. Implement retry logic with exponential backoff
4. Monitor queue depths
5. Set appropriate message TTLs
"""
        },
        {
            "name": "Python Async/Await Patterns",
            "description": "Common patterns and best practices for async Python code",
            "category": "Python",
            "content": """# Python Async/Await Patterns

## Basic Async Function

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return "Data fetched"

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

## Running Multiple Tasks Concurrently

```python
async def fetch_user(user_id):
    await asyncio.sleep(1)
    return f"User {user_id}"

async def main():
    # Run concurrently
    users = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3)
    )
    print(users)

asyncio.run(main())
```

## Error Handling

```python
async def risky_operation():
    try:
        await some_async_call()
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise

async def with_timeout():
    try:
        await asyncio.wait_for(
            risky_operation(),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        print("Operation timed out")
```

## Context Manager Pattern

```python
class AsyncResource:
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

async def use_resource():
    async with AsyncResource() as resource:
        await resource.do_something()
```
"""
        },
        {
            "name": "FastAPI Best Practices",
            "description": "Production-ready patterns for FastAPI applications",
            "category": "Web Development",
            "content": """# FastAPI Best Practices

## Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── routers/
│   │   ├── users.py
│   │   └── items.py
│   └── dependencies.py
├── tests/
├── requirements.txt
└── README.md
```

## Dependency Injection

```python
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Error Handling

```python
from fastapi import HTTPException, status

class ItemNotFoundError(Exception):
    pass

@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Item not found"}
    )
```

## Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Send email logic
    pass

@app.post("/send-notification/")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, "Thank you!")
    return {"message": "Notification will be sent"}
```
"""
        },
        {
            "name": "Git Workflow Guide",
            "description": "Team Git workflow and branching strategy",
            "category": "Version Control",
            "content": """# Git Workflow Guide

## Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Emergency fixes

## Feature Development

```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# Work on feature
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
```

## Commit Message Convention

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

## Useful Commands

```bash
# Interactive rebase
git rebase -i HEAD~3

# Amend last commit
git commit --amend

# Stash changes
git stash save "work in progress"
git stash pop

# Cherry pick
git cherry-pick <commit-hash>
```
"""
        }
    ]
    
    for resource in resources:
        created = db.create_resource(resource)
        print(f"  ✓ Created resource: {created['name']} ({created['id']})")
    
    # ===== Seed Tools =====
    print("\n🛠️  Creating tools...")
    
    tools = [
        {
            "name": "Database Backup Script",
            "description": "Creates a timestamped backup of PostgreSQL database",
            "code": """#!/bin/bash
# PostgreSQL Database Backup Script

DB_NAME="myapp_db"
DB_USER="postgres"
BACKUP_DIR="/var/backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
""",
            "tags": ["database", "backup", "postgresql", "bash"]
        },
        {
            "name": "Log Analyzer",
            "description": "Python script to analyze application logs for errors and patterns",
            "code": """#!/usr/bin/env python3
import re
from collections import Counter
from datetime import datetime

def analyze_logs(log_file):
    \"\"\"Analyze log file for errors and patterns\"\"\"
    
    error_pattern = re.compile(r'ERROR|CRITICAL|FATAL')
    errors = []
    error_types = Counter()
    
    with open(log_file, 'r') as f:
        for line in f:
            if error_pattern.search(line):
                errors.append(line.strip())
                # Extract error type
                match = re.search(r'(\\w+Error|\\w+Exception)', line)
                if match:
                    error_types[match.group(1)] += 1
    
    print(f"Total errors found: {len(errors)}")
    print("\\nTop error types:")
    for error_type, count in error_types.most_common(10):
        print(f"  {error_type}: {count}")
    
    return errors, error_types

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python log_analyzer.py <log_file>")
        sys.exit(1)
    
    analyze_logs(sys.argv[1])
""",
            "tags": ["logging", "monitoring", "python", "debugging"]
        },
        {
            "name": "API Health Checker",
            "description": "Monitor API endpoint health and response times",
            "code": """#!/usr/bin/env python3
import requests
import time
from datetime import datetime

def check_endpoint(url, timeout=5):
    \"\"\"Check if an endpoint is healthy\"\"\"
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        elapsed_time = (time.time() - start_time) * 1000  # ms
        
        status = "✓ UP" if response.status_code == 200 else "✗ DOWN"
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        print(f"  URL: {url}")
        print(f"  Status: {status} (HTTP {response.status_code})")
        print(f"  Response Time: {elapsed_time:.2f}ms")
        print()
        
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print(f"✗ TIMEOUT: {url}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ ERROR: {url} - {str(e)}")
        return False

def monitor_endpoints(endpoints, interval=60):
    \"\"\"Continuously monitor multiple endpoints\"\"\"
    while True:
        print("=" * 50)
        for endpoint in endpoints:
            check_endpoint(endpoint)
        
        print(f"Waiting {interval} seconds before next check...")
        time.sleep(interval)

if __name__ == "__main__":
    endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/api/status"
    ]
    
    monitor_endpoints(endpoints, interval=30)
""",
            "tags": ["monitoring", "api", "health-check", "python"]
        },
        {
            "name": "Docker Cleanup",
            "description": "Clean up unused Docker resources to free disk space",
            "code": """#!/bin/bash
# Docker Cleanup Script

echo "🧹 Docker Cleanup Starting..."
echo

# Remove stopped containers
echo "Removing stopped containers..."
docker container prune -f

# Remove unused images
echo "Removing unused images..."
docker image prune -a -f

# Remove unused volumes
echo "Removing unused volumes..."
docker volume prune -f

# Remove unused networks
echo "Removing unused networks..."
docker network prune -f

# Remove build cache
echo "Removing build cache..."
docker builder prune -a -f

echo
echo "✅ Cleanup complete!"
echo
echo "Current disk usage:"
docker system df
""",
            "tags": ["docker", "cleanup", "maintenance", "bash"]
        }
    ]
    
    for tool in tools:
        created = db.create_tool(tool)
        print(f"  ✓ Created tool: {created['name']} ({created['id']})")
    
    print("\n✅ Database seeded successfully!")
    print(f"\nSummary:")
    print(f"  - Prompts: {len(db.get_all_prompts())}")
    print(f"  - Resources: {len(db.get_all_resources())}")
    print(f"  - Tools: {len(db.get_all_tools())}")


if __name__ == "__main__":
    seed_database()

