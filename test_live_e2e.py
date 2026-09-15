import asyncio
import httpx
import json
import sys

async def test_endpoint(message: str, model: str = "qwen2.5:0.5b", skill: str = ""):
    print(f"\n{'='*60}")
    print(f"Testing Query: '{message}'")
    print(f"{'='*60}")
    
    url = "http://localhost:8000/api/chat"
    payload = {
        "message": message,
        "history": [],
        "model": model,
        "skill": skill
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    print(f"❌ Error: HTTP {response.status_code}")
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            event = json.loads(data_str)
                            if event["type"] == "status":
                                print(f"ℹ️ Status: {event['message']}")
                            elif event["type"] == "citations":
                                citations_count = len(event.get("citations", []))
                                print(f"📚 Retrieved {citations_count} citations")
                            elif event["type"] == "token":
                                print(event["token"], end="", flush=True)
                            elif event["type"] == "done":
                                pass
                        except json.JSONDecodeError:
                            pass
        print("\n\n✅ Stream completed successfully.")
        return True
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        return False

async def main():
    # Fix for windows emoji printing
    sys.stdout.reconfigure(encoding='utf-8')
    print("🚀 Starting E2E Functional Tests against Live Server...")
    
    # Test 1: Standard QA Retrieval
    await test_endpoint("What are the 5 components of product positioning according to April Dunford?")
    
    # Test 2: Artifact Generation (using explicit keyword to trigger artifact/html)
    await test_endpoint("Create an interactive HTML UI scorecard for Gibson Biddle's DHM model")
    
    # Test 3: Out-of-domain Guardrail
    await test_endpoint("What are the best stocks to invest in for 2026?")
    
    print("\n🏁 All live tests completed.")

if __name__ == "__main__":
    asyncio.run(main())
