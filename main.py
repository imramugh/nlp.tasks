"""
Author: Imran Mughal
Email: imran@mughal.com
Date: December 19, 2024
"""

import os
from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import json
from contextlib import asynccontextmanager

from async_db import engine, AsyncSessionLocal, get_session
from nlp_processor import NLPProcessor
from models import Base

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Task Management MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NLP processor
nlp_processor = NLPProcessor(os.getenv("OPENAI_API_KEY"))

# Create database tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Create a new session for each request
            session = AsyncSessionLocal()
            try:
                # Process the natural language query
                result = await nlp_processor.process_query(data, session)
                await session.commit()
                
                # Send response back to client
                await websocket.send_text(json.dumps({
                    "success": True,
                    "response": result.get("response", ""),
                    "data": result.get("data", None)
                }))
            except Exception as query_error:
                await session.rollback()
                # Handle query-specific errors
                await websocket.send_text(json.dumps({
                    "success": False,
                    "response": f"Error processing query: {str(query_error)}",
                    "data": None
                }))
            finally:
                await session.close()
    
    except Exception as e:
        # Handle connection errors
        try:
            await websocket.send_text(json.dumps({
                "success": False,
                "response": f"Connection error: {str(e)}",
                "data": None
            }))
        except:
            pass  # If we can't send the error, just pass
    finally:
        try:
            await websocket.close()
        except:
            pass  # If we can't close cleanly, just pass

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Example REST endpoint for direct task creation
@app.post("/tasks")
async def create_task(task_data: dict, session: AsyncSession = Depends(get_session)):
    try:
        result = await nlp_processor.process_query(
            f"Create a task with title '{task_data['title']}' "
            f"and description '{task_data.get('description', '')}'",
            session
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    ) 