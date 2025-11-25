#!/usr/bin/env python3
"""
Demonstration script for the Smart MCP HTTP API.
"""
from __future__ import annotations

import requests

BASE_URL = "http://localhost:8000"
API_ROOT = f"{BASE_URL}/api/v1"


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"{title}")
    print("=" * 60)


def check_health() -> bool:
    print_section("Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"❌ Server not available: {exc}")
        print("   Start it via: python run_server.py")
        return False
    data = resp.json()
    print(f"✅ Status: {data['status']} at {data['timestamp']}")
    return True


def list_prompts() -> None:
    print_section("List Prompts")
    resp = requests.get(f"{API_ROOT}/prompts")
    resp.raise_for_status()
    prompts = resp.json()
    if not prompts:
        print("No prompts stored yet.")
        return
    for prompt in prompts:
        print(f"• {prompt['name']} ({prompt['role']}) - tags: {prompt['tags']}")


def create_prompt() -> str | None:
    print_section("Create Prompt")
    payload = {
        "name": "Demo Prompt",
        "role": "system",
        "content": "You are a helpful assistant that answers in 2 bullet points.",
        "tags": ["demo", "mcp"],
    }
    resp = requests.post(f"{API_ROOT}/prompts", json=payload)
    if resp.status_code != 201:
        print(f"Failed to create prompt: {resp.text}")
        return None
    prompt = resp.json()
    print(f"✅ Created prompt {prompt['id']}")
    return prompt["id"]


def semantic_search(query: str = "database") -> None:
    print_section("Semantic Search")
    resp = requests.get(f"{API_ROOT}/search", params={"q": query})
    resp.raise_for_status()
    body = resp.json()
    print(f"Query: {body['query']}")
    for result in body["results"]:
        print(f"• {result['type']} ({result['score']:.3f}): {result['payload']['name']}")


def delete_prompt(prompt_id: str) -> None:
    print_section("Cleanup Prompt")
    resp = requests.delete(f"{API_ROOT}/prompts/{prompt_id}")
    if resp.status_code == 204:
        print(f"🧹 Deleted prompt {prompt_id}")
    else:
        print(f"Failed to delete prompt {prompt_id}: {resp.text}")


def show_mcp_methods() -> None:
    print_section("MCP Root Info")
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    data = resp.json()
    print(f"Server: {data['name']} - protocol {data['version']}")
    print("Available MCP JSON-RPC methods:")
    for method in data["capabilities"].keys():
        print(f"• {method}")


def main() -> None:
    if not check_health():
        return
    list_prompts()
    created_id = create_prompt()
    semantic_search()
    show_mcp_methods()
    if created_id:
        delete_prompt(created_id)
    print_section("Demo Complete")


if __name__ == "__main__":
    main()

