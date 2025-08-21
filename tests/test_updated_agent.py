#!/usr/bin/env python3
"""Test script for the updated GitHubAgent using mcp_use."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_git_projects.agent import GitHubAgent

def test_sync_execution():
    """Test synchronous execution of the GitHubAgent."""
    print("Testing GitHubAgent with synchronous execution...")
    
    try:
        # Initialize agent with config file
        agent = GitHubAgent(
            config_file="github_mcp.json",
            model_name="google/gemini-2.5-flash-lite",
            max_steps=30
        )
        
        # Test query
        result = agent.run_sync("List the first 3 repositories for user seszele64 with their descriptions")
        print("Result:")
        print(result)
        
        # Clean up
        agent.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def test_async_execution():
    """Test asynchronous execution of the GitHubAgent."""
    print("\nTesting GitHubAgent with asynchronous execution...")
    
    try:
        # Initialize agent with config file
        agent = GitHubAgent(
            config_file="github_mcp.json",
            model_name="google/gemini-2.5-flash-lite",
            max_steps=30
        )
        
        # Test query
        result = await agent.run_async("Get details about the 'analyze-git-projects' repository for user seszele64")
        print("Result:")
        print(result)
        
        # Clean up
        agent.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_context_manager():
    """Test GitHubAgent as a context manager."""
    print("\nTesting GitHubAgent as context manager...")
    
    try:
        with GitHubAgent(config_file="github_mcp.json") as agent:
            result = agent.run_sync("What programming languages are used in seszele64's repositories?")
            print("Result:")
            print(result)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing updated GitHubAgent...")
    
    # Test sync execution
    test_sync_execution()
    
    # Test async execution
    asyncio.run(test_async_execution())
    