import asyncio
import websockets
import json

async def test_natural_language_queries():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Test queries
        queries = [
            "Create a new task called 'Review documentation' with high priority",
            "Show me all high priority tasks",
            "Create a task 'Update README' due tomorrow",
            "What are all my pending tasks?",
        ]
        
        for query in queries:
            print(f"\nSending query: {query}")
            await websocket.send(query)
            response = await websocket.recv()
            print(f"Received response: {json.loads(response)}")
            await asyncio.sleep(1)  # Small delay between queries

if __name__ == "__main__":
    asyncio.run(test_natural_language_queries()) 