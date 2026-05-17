from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .connection_manager import manager
from .conversation import stream_ai_response, analyze_and_save_transcript
from .prompts import INITIAL_GREETING
from .retry import startup_retry

app = FastAPI(title="HR Interview Agent")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/interview/hr/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await manager.connect(session_id, websocket)

    # Send initial greeting
    await manager.send_message(INITIAL_GREETING, session_id)

    try:
        while True:
            user_message = await websocket.receive_text()

            # Stream the response back to the user
            async for chunk in stream_ai_response(session_id, user_message):
                await manager.send_message(chunk, session_id)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Client #{session_id} disconnected. Starting post-interview analysis.")
        # Perform post-interview analysis
        await analyze_and_save_transcript(session_id, user_id)
