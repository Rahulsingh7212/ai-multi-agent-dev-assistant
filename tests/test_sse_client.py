"""
Simple SSE client for testing streaming endpoint.
Run in a separate terminal while server is running.
"""
import httpx
import json
import asyncio


async def test_sse():
    url = "http://127.0.0.1:8000/api/v1/chat"
    payload = {
        "message": "What are the 4 pillars of OOP?",
        "stream": True
    }

    print("🟢 Connecting to SSE stream...\n")

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", url,
            json=payload,
            timeout=30.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line.replace("data: ", ""))
                    if "content" in data:
                        print(data["content"], end="", flush=True)
                    elif "session_id" in data and "total_chars" in data:
                        print(f"\n\n🏁 Stream complete — {data['total_chars']} chars")

    print("\n\n✅ SSE test complete!")


if __name__ == "__main__":
    asyncio.run(test_sse())