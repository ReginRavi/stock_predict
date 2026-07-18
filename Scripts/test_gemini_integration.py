#!/usr/bin/env python3
"""
Test script to verify Gemini API integration in agent.py
"""

import asyncio
import os
from agent import build_agent
from models import ChatRequest, TimeWindow

async def test_gemini_integration():
    """Test the Gemini API integration"""
    print("Testing Gemini API Integration")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set - will use fallback response")
    else:
        print(f"✅ GEMINI_API_KEY is configured")
    
    # Build agent
    print("\nBuilding agent...")
    agent = build_agent()
    await agent.startup()
    
    # Create a test request
    print("\nCreating test request...")
    request = ChatRequest(
        question="Why is my service experiencing high latency?",
        service="api-gateway",
        namespace="production",
        severity_hint="warning",
        time_window=TimeWindow(lookback_minutes=30)
    )
    
    # Handle the chat request
    print("\nProcessing request...")
    try:
        response = await agent.handle_chat(request)
        
        print("\n" + "=" * 60)
        print("RESPONSE")
        print("=" * 60)
        print(f"\nAnswer:\n{response.answer}")
        print(f"\nFindings: {len(response.findings)}")
        for i, finding in enumerate(response.findings, 1):
            print(f"  {i}. {finding}")
        
        print(f"\nTool Results:")
        for tool_name, result in response.tool_results.items():
            print(f"  - {tool_name}: {result.status}")
        
        if response.metadata:
            print(f"\nMetadata:")
            print(f"  - Latency: {response.metadata.latency_ms}ms")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(test_gemini_integration())
